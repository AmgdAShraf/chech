from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
import threading
from queue import Queue
import shutil # لاستخدام shutil.rmtree لحذف المجلدات
import sys # لإضافة ميزات للتحقق من مسار Chrome

# قفل للكتابة في الملفات لمنع تعارضات الوصول (Race Conditions)
file_lock = threading.Lock()

def check_account_status(username, driver):
    url = f"https://twitter.com/{username}"
    try:
        driver.get(url)
        time.sleep(4) # وقت انتظار أطول لضمان تحميل الصفحة على تويتر
        page_source = driver.page_source.lower()

        if "account suspended" in page_source:
            return "suspended"
        elif "this account doesn’t exist" in page_source or "doesn't exist" in page_source:
            return "suspended"
        elif "followers" in page_source or "following" in page_source:
            return "live"
        else:
            return "unknown"
    except Exception as e:
        # هنا قد يحدث خطأ إذا فشل الدرايفر بعد بدء التشغيل (مثل انقطاع الاتصال)
        print(f"❌ خطأ في الحساب {username} أثناء التحقق: {e}")
        return "error"

def find_chrome_executable():
    """يحاول العثور على المسار التنفيذي لمتصفح Chrome."""
    if sys.platform == "win32":
        # مسارات افتراضية لـ Chrome على Windows
        paths = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            os.path.join(os.getenv("LOCALAPPDATA"), "Google\\Chrome\\Application\\chrome.exe"),
            os.path.join(os.getenv("PROGRAMFILES"), "Google\\Chrome\\Application\\chrome.exe")
        ]
        for path in paths:
            if os.path.exists(path):
                print(f"✅ تم العثور على Chrome في: {path}")
                return path
    # يمكنك إضافة مسارات لأنظمة تشغيل أخرى هنا (مثل Linux أو macOS)
    
    # إذا لم يتم العثور عليه في المسارات الافتراضية، يمكننا المحاولة بالمسار الذي ذكره Selenium في الخطأ
    print("⚠️ لم يتم العثور على Chrome في المسارات الافتراضية. سأعتمد على المسار الذي يفترضه ChromeDriver.")
    # يمكن أن يكون المسار الذي أشار إليه Selenium في خطأك: C:\Program Files\Google\Chrome\Application\chrome.exe
    # بما أنك قلت أنه مازال يفشل، فسنتركه بدون تحديد صريح إذا لم يعثر عليه
    return None

def worker(q, live_file, suspended_file, chrome_path, thread_id, chrome_binary_location):
    """دالة العامل لكل ثريد، تدير مثيل WebDriver الخاص بها."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # تشغيل المتصفح بدون واجهة رسومية
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1000,800")
    chrome_options.add_argument(f"--user-data-dir=./chrome_profile_{thread_id}")

    # خيارات إضافية للثبات ومحاولة حل مشكلة DevToolsActivePort
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")  # كبت معظم رسائل السجل
    chrome_options.add_argument("--incognito")  # بدء وضع التصفح المتخفي
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # تعطيل وضع التشغيل الآلي الذي يمكن أن تكتشفه المواقع
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # تحديد مسار Chrome التنفيذي بشكل صريح إذا تم العثور عليه
    if chrome_binary_location:
        chrome_options.binary_location = chrome_binary_location
        print(f"✅ Thread {thread_id}: تم تحديد مسار Chrome التنفيذي: {chrome_binary_location}")
    else:
        print(f"⚠️ Thread {thread_id}: لم يتم تحديد مسار Chrome التنفيذي بشكل صريح. سيعتمد ChromeDriver على البحث التلقائي.")

    service = Service(executable_path=chrome_path)
    driver = None  # تهيئة الدرايفر إلى None

    try:
        print(f"🔍 Thread {thread_id}: محاولة تشغيل متصفح Chrome...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"✅ Thread {thread_id}: تم تشغيل المتصفح بنجاح.")

        while True:
            try:
                line_data = q.get(timeout=1)  # احصل على عنصر من الطابور، مع مهلة
                if line_data is None:  # قيمة إشارة لإخبار الثريد بالخروج
                    break

                original_line, username, idx = line_data

                print(f"[Thread {thread_id}][{idx}] 🔍 فحص الحساب: {username}")
                status = check_account_status(username, driver)

                status = status.strip().lower()
                print(f"[Thread {thread_id}][{idx}] ✅ الحساب: {username} - الحالة: {status}")

                result_line = f"{original_line}\n"

                with file_lock:  # الحصول على القفل قبل الكتابة في الملفات
                    if status == "live":
                        live_file.write(result_line)
                        live_file.flush()
                    elif status == "suspended":
                        suspended_file.write(result_line)
                        suspended_file.flush()
                    else:
                        print(f"[Thread {thread_id}][{idx}] ⚠️ الحالة غير واضحة أو فشل: {status}")

                q.task_done()
            except Queue.Empty:
                # لا توجد عناصر أخرى في الطابور، يمكن للثريد الخروج
                break
            except Exception as e:
                print(f"❌ Thread {thread_id}: خطأ أثناء معالجة عنصر من الطابور: {e}")
                q.task_done()  # ضع علامة على المهمة كمكتملة حتى لو حدث خطأ لمنع الجمود

    except Exception as e:
        print(f"❌ Thread {thread_id}: فشل في تشغيل متصفح Chrome. يرجى التأكد من توافق ChromeDriver مع إصدار Chrome لديك. الخطأ: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                print(f"⚠️ Thread {thread_id}: خطأ أثناء إغلاق المتصفح: {e}")
        print(f"Thread {thread_id}: تم إغلاق المتصفح.")


def main():
    input_file = "accounts.txt"
    output_live = "live_accounts.txt"
    output_suspended = "suspended_accounts.txt"

    num_threads = int(input("أدخل عدد الثريدات (الخيوط) التي تريد استخدامها: "))
    if num_threads <= 0:
        print("عدد الثريدات يجب أن يكون أكبر من صفر.")
        return

    # تنظيف مجلدات ملفات تعريف Chrome القديمة قبل البدء
    print("🧹 جاري حذف ملفات تعريف Chrome المؤقتة القديمة...")
    for i in range(1, num_threads + 1):
        profile_dir = f"./chrome_profile_{i}"
        if os.path.exists(profile_dir):
            try:
                shutil.rmtree(profile_dir)
                print(f"🧹 تم حذف مجلد الملف الشخصي القديم: {profile_dir}")
            except OSError as e:
                print(f"⚠️ لا يمكن حذف مجلد الملف الشخصي {profile_dir}: {e}")
    print("🧹 انتهى حذف الملفات.")

    live_file = open(output_live, "w", encoding="utf-8")
    suspended_file = open(output_suspended, "w", encoding="utf-8")

    chrome_path = "chromedriver.exe"
    if not os.path.isfile(chrome_path):
        print(f"❌ ملف ChromeDriver غير موجود في نفس مجلد السكريبت.")
        return
    
    # تحديد مسار Chrome التنفيذي
    chrome_binary_location = find_chrome_executable()
    if not chrome_binary_location:
        # إذا لم يتم العثور عليه تلقائيًا، يمكن للمستخدم إدخاله يدويًا
        print("\n⚠ لم نتمكن من العثور على المسار التنفيذي لـ Google Chrome تلقائيًا.")
        print("يرجى إدخال المسار الكامل لملف 'chrome.exe' (مثال: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe):")
        manual_path = input("مسار Chrome: ").strip()
        if os.path.exists(manual_path):
            chrome_binary_location = manual_path
            print(f"✅ تم استخدام المسار اليدوي: {chrome_binary_location}")
        else:
            print("❌ المسار اليدوي غير صالح. سيعتمد ChromeDriver على البحث التلقائي وقد يفشل.")


    account_queue = Queue()

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total_accounts = 0
    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        username = line.split(":")[0] if ":" in line else line
        account_queue.put((line, username, idx))
        total_accounts += 1
    
    if total_accounts == 0:
        print("❌ ملف الحسابات فارغ أو لا يحتوي على حسابات صالحة.")
        live_file.close()
        suspended_file.close()
        return


    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(account_queue, live_file, suspended_file, chrome_path, i+1, chrome_binary_location))
        threads.append(thread)
        thread.start()

    # انتظر حتى يتم معالجة جميع المهام في الطابور
    account_queue.join()

    # أضف قيم إشارة (None) إلى الطابور لإخبار الثريدات العاملة بالخروج
    for _ in range(num_threads):
        account_queue.put(None)

    # انتظر حتى تنتهي جميع الثريدات
    for thread in threads:
        thread.join()

    live_file.close()
    suspended_file.close()

    print("\n📊 ملخص الفحص:")
    print(f"🔢 عدد الحسابات المفحوصة: {total_accounts}")
    # ملاحظة: للحصول على العدد الدقيق للحسابات الحية/الموقوفة، قد تحتاج إلى إعادة قراءة ملفات الإخراج أو تنفيذ عدادات مشتركة محمية بأقفال.
    print(f"📁 تم حفظ النتائج في:\n- {output_live}\n- {output_suspended}")


if __name__ == "__main__":
    main()