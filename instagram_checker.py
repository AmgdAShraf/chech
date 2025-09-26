from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os

def check_account_status(username, driver):
    url = f"https://www.instagram.com/{username}/"
    try:
        driver.get(url)
        time.sleep(4)
        page_source = driver.page_source.lower()

        if "sorry, this page isn't available" in page_source:
            return "suspended"
        elif "log in" in page_source and "see photos and videos" in page_source:
            return "live"
        elif "followers" in page_source or "following" in page_source:
            return "live"
        else:
            return "unknown"
    except Exception as e:
        print(f"❌ خطأ في الحساب {username}: {e}")
        return "error"

def main():
    input_file = "accounts.txt"
    output_live = "live_accounts.txt"
    output_suspended = "suspended_accounts.txt"

    live_file = open(output_live, "w", encoding="utf-8")
    suspended_file = open(output_suspended, "w", encoding="utf-8")

    chrome_path = "chromedriver.exe"
    if not os.path.isfile(chrome_path):
        print(f"❌ ملف ChromeDriver غير موجود في نفس مجلد السكريبت.")
        return

    chrome_options = Options()
    # chrome_options.add_argument("--headless")  ← شيل التعليق لو تحب تشغيل خفي
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1000,800")

    service = Service(executable_path=chrome_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("✅ تم تشغيل المتصفح بنجاح، جاري فحص حسابات إنستجرام...\n")

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    total = 0
    live_count = 0
    suspended_count = 0

    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        username = line.split(":")[0] if ":" in line else line
        total += 1

        print(f"[{idx}] 🔍 فحص الحساب: {username}")
        status = check_account_status(username, driver)

        status = status.strip().lower()
        print(f"[{idx}] ✅ الحساب: {username} - الحالة: {status}")

        result_line = f"{line}\n"

        if status == "live":
            live_file.write(result_line)
            live_file.flush()
            live_count += 1
        elif status == "suspended":
            suspended_file.write(result_line)
            suspended_file.flush()
            suspended_count += 1
        else:
            print(f"[{idx}] ⚠️ الحالة غير واضحة أو فشل: {status}")

        time.sleep(2)

    driver.quit()
    live_file.close()
    suspended_file.close()

    print("\n📊 ملخص الفحص:")
    print(f"🔢 عدد الحسابات المفحوصة: {total}")
    print(f"✅ الحسابات الحية (Live): {live_count}")
    print(f"❌ الحسابات المحذوفة أو المقفولة (Suspended): {suspended_count}")
    print(f"📁 تم حفظ النتائج في:\n- {output_live}\n- {output_suspended}")

if __name__ == "__main__":
    main()
