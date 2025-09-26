import requests
from bs4 import BeautifulSoup
import time
import random

class SocialMediaChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def check_instagram(self, username):
        """فحص حساب Instagram"""
        try:
            url = f"https://www.instagram.com/{username}/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 404:
                return "suspended"
            elif response.status_code == 200:
                content = response.text.lower()
                if "sorry, this page isn't available" in content:
                    return "suspended"
                elif "followers" in content or "following" in content:
                    return "live"
                else:
                    return "unknown"
            else:
                return "error"
                
        except Exception as e:
            print(f"خطأ في فحص Instagram {username}: {e}")
            return "error"
    
    def check_twitter(self, username):
        """فحص حساب Twitter"""
        try:
            url = f"https://twitter.com/{username}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 404:
                return "suspended"
            elif response.status_code == 200:
                content = response.text.lower()
                if "account suspended" in content or "doesn't exist" in content:
                    return "suspended"
                elif "followers" in content or "following" in content:
                    return "live"
                else:
                    return "unknown"
            else:
                return "error"
                
        except Exception as e:
            print(f"خطأ في فحص Twitter {username}: {e}")
            return "error"
    
    def check_tiktok(self, username):
        """فحص حساب TikTok"""
        try:
            url = f"https://www.tiktok.com/@{username}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 404:
                return "suspended"
            elif response.status_code == 200:
                content = response.text.lower()
                if "couldn't find this account" in content:
                    return "suspended"
                elif "followers" in content or "following" in content:
                    return "live"
                else:
                    return "unknown"
            else:
                return "error"
                
        except Exception as e:
            print(f"خطأ في فحص TikTok {username}: {e}")
            return "error"
    
    def check_accounts(self, accounts, platform, progress_callback=None):
        """فحص قائمة من الحسابات"""
        results = []
        total = len(accounts)
        
        for i, account in enumerate(accounts):
            # استخراج اسم المستخدم من السطر
            username = account.split(":")[0].strip() if ":" in account else account.strip()
            
            if not username:
                continue
            
            # اختيار دالة الفحص المناسبة
            if platform == "Instagram":
                status = self.check_instagram(username)
            elif platform == "Twitter":
                status = self.check_twitter(username)
            elif platform == "TikTok":
                status = self.check_tiktok(username)
            else:
                status = "error"
            
            results.append({
                'original_line': account.strip(),
                'username': username,
                'status': status,
                'platform': platform
            })
            
            # تحديث شريط التقدم
            if progress_callback:
                progress_callback(i + 1, total, username, status)
            
            # توقف قصير لتجنب الحظر
            time.sleep(random.uniform(1, 2))
        
        return results