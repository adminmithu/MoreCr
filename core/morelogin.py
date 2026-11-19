import time
import json
import base64
import hashlib
import re
import random
import string
import requests
import asyncio
from datetime import datetime
from typing import Callable, Optional, Tuple, Dict, Any
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from config import (
    MORELOGIN_CODEC_BASE,
    MORELOGIN_REGISTER_URL,
    MUELLFACH_API_URL,
    MUELLFACH_SYNC_URL,
    MUELLFACH_DOMAIN
)

class LiveAutomationTracker:
    """Tracks live automation state for real-time visualization on the web dashboard"""
    def __init__(self):
        self.state = {
            "status": "idle",  # "idle", "running", "success", "error"
            "step": 0,
            "step_title": "Ready for automation",
            "url": "https://www.morelogin.com/register",
            "active_tab": "morelogin",  # "morelogin" or "muellfach"
            "email": "",
            "password": "",
            "mailbox_url": "",
            "logs": [
                f"[{datetime.now().strftime('%H:%M:%S')}] Live Automation Engine Initialized."
            ],
            "last_updated": time.time()
        }

    def set_step(self, step: int, step_title: str, url: str, active_tab: str,
                 email: str = "", password: str = "", mailbox_url: str = "", log_msg: str = ""):
        self.state["status"] = "running"
        self.state["step"] = step
        self.state["step_title"] = step_title
        self.state["url"] = url
        self.state["active_tab"] = active_tab
        if email:
            self.state["email"] = email
        if password:
            self.state["password"] = password
        if mailbox_url:
            self.state["mailbox_url"] = mailbox_url
        if log_msg:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.state["logs"].append(f"[{timestamp}] {log_msg}")
            if len(self.state["logs"]) > 25:
                self.state["logs"].pop(0)
        self.state["last_updated"] = time.time()

    def set_success(self, email: str, password: str, mailbox_url: str):
        self.state["status"] = "success"
        self.state["step"] = 5
        self.state["step_title"] = "Account 100% Activated & Ready!"
        self.state["email"] = email
        self.state["password"] = password
        self.state["mailbox_url"] = mailbox_url
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.state["logs"].append(f"[{timestamp}] 🎉 MoreLogin Account ({email}) activated successfully!")
        self.state["last_updated"] = time.time()

    def set_error(self, err_msg: str):
        self.state["status"] = "error"
        self.state["step_title"] = f"Failed: {err_msg}"
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.state["logs"].append(f"[{timestamp}] ❌ Error encountered: {err_msg}")
        self.state["last_updated"] = time.time()

    def get_state(self) -> Dict[str, Any]:
        return dict(self.state)

# Global tracker instance
live_tracker = LiveAutomationTracker()

class MoreLoginCreator:
    def __init__(self):
        self.key = MORELOGIN_CODEC_BASE[:16].encode('utf-8')
        self.iv = MORELOGIN_CODEC_BASE[-16:].encode('utf-8')

    def create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        })
        return session

    def encrypt_data(self, data_dict: dict) -> str:
        json_str = json.dumps(data_dict, separators=(',', ':'))
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded = pad(json_str.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt_data(self, b64_str: str) -> str:
        encrypted = base64.b64decode(b64_str)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted = cipher.decrypt(encrypted)
        return unpad(decrypted, AES.block_size).decode('utf-8')

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.md5((password + ".corebrowser").encode('utf-8')).hexdigest()

    @staticmethod
    def generate_random_email(prefix: str = "priyaahmed210208") -> str:
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        clean_prefix = prefix.split('@')[0].strip()
        if not clean_prefix:
            clean_prefix = "priyaahmed210208"
        return f"{clean_prefix}_{suffix}@{MUELLFACH_DOMAIN}"

    def register_on_morelogin(self, session: requests.Session, email: str, password: str) -> Tuple[bool, str, Dict[str, Any]]:
        hashed_pwd = self.hash_password(password)
        payload = {
            "username": email,
            "userEmail": email,
            "userPassword": hashed_pwd,
            "verificationCode": "",
            "captcha": "",
            "affiliateCode": "",
            "cueCode": "",
            "is_ignore_promoter": True
        }

        encrypted_body = self.encrypt_data(payload)
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "super-version": "",
            "super-lang": "",
            "client-platform": "",
            "x-version": "",
            "x-os": "",
            "accept-language": "en",
            "x-time-zone": "Asia/Dhaka",
            "x-is-devops": "",
            "Origin": "https://www.morelogin.com",
            "Referer": "https://www.morelogin.com/register"
        }

        try:
            resp = session.post(
                MORELOGIN_REGISTER_URL,
                data=encrypted_body.encode('utf-8'),
                headers=headers,
                timeout=20
            )
            resp_text = resp.text.strip()
            if not resp_text:
                return False, f"Server returned empty response (Status: {resp.status_code})", {}

            try:
                decrypted_json_str = self.decrypt_data(resp_text)
                data = json.loads(decrypted_json_str)
            except Exception:
                data = resp.json()

            code = data.get("code")
            msg = data.get("msg") or "Success"

            if code == 0 or data.get("success") is True:
                return True, "Registration initiated! Activation email sent.", data
            else:
                return False, f"MoreLogin Error ({code}): {msg}", data

        except requests.RequestException as e:
            return False, f"Network error during MoreLogin registration: {str(e)}", {}

    def sync_muellfach(self, session: requests.Session) -> None:
        try:
            session.get(MUELLFACH_SYNC_URL, timeout=6)
        except Exception:
            pass

    def check_muellfach_emails(self, session: requests.Session, email: str) -> list:
        try:
            resp = session.get(
                f"{MUELLFACH_API_URL}?action=mails&address={email}",
                timeout=10
            )
            data = resp.json()
            if data.get("status") == "ok":
                return data.get("mails", [])
        except Exception:
            pass
        return []

    def get_email_details(self, session: requests.Session, email: str, mail_id: int) -> Optional[dict]:
        try:
            resp = session.get(
                f"{MUELLFACH_API_URL}?action=mail&id={mail_id}&address={email}",
                timeout=10
            )
            data = resp.json()
            if data.get("status") == "ok":
                return data.get("mail")
        except Exception:
            pass
        return None

    def poll_for_activation_link(self, session: requests.Session, email: str, timeout_seconds: int = 40, poll_interval: int = 3) -> Optional[str]:
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            self.sync_muellfach(session)
            mails = self.check_muellfach_emails(session, email)
            for m in mails:
                sender = (m.get("sender_email") or "") + (m.get("sender_name") or "")
                subject = m.get("subject") or ""
                if "morelogin" in sender.lower() or "morelogin" in subject.lower() or "activate" in subject.lower():
                    mail_id = m.get("id")
                    details = self.get_email_details(session, email, mail_id)
                    if details:
                        body_html = details.get("body_html") or ""
                        body_text = details.get("body_text") or ""
                        combined = body_html + " " + body_text

                        match = re.search(r'href=["\'](https://cb-gateway\.morelogin\.com/app/member/activate\?token=[^"\'\s>]+)["\']', combined)
                        if not match:
                            match = re.search(r'(https://cb-gateway\.morelogin\.com/app/member/activate\?token=[^\s"\'<>]+)', combined)

                        if match:
                            return match.group(1).replace("&amp;", "&")

            time.sleep(poll_interval)
        return None

    def activate_account(self, session: requests.Session, activation_link: str) -> bool:
        try:
            resp = session.get(activation_link, timeout=12, allow_redirects=True)
            return resp.status_code == 200
        except Exception:
            return False

    async def create_account_full_flow(
        self,
        email_prefix: str,
        password: str,
        progress_callback: Optional[Callable[[str], Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes full account creation flow while updating live visual browser state:
        1. Open MoreLogin tab
        2. Generate muellfach.de email & fill credentials
        3. Submit registration to MoreLogin Gateway
        4. Switch to muellfach.de inbox tab & poll for email
        5. Click activation link
        6. Complete & report success
        """
        async def update_status(text: str):
            if progress_callback:
                if asyncio.iscoroutinefunction(progress_callback):
                    await progress_callback(text)
                else:
                    progress_callback(text)

        loop = asyncio.get_running_loop()
        session = self.create_session()

        # Step 1: Open MoreLogin Register page
        live_tracker.set_step(
            step=1,
            step_title="Opening MoreLogin Register Tab",
            url="https://www.morelogin.com/register",
            active_tab="morelogin",
            log_msg="Opening web browser tab: https://www.morelogin.com/register"
        )
        await update_status("⚡ [1/4] MoreLogin রেজিস্ট্রেশন পেইজ ওপেন করা হচ্ছে...")
        await asyncio.sleep(0.8)

        # Step 2: Generate Email & Fill Credentials
        email = self.generate_random_email(email_prefix)
        mailbox_name = email.split('@')[0]
        mailbox_url = f"https://www.muellfach.de/postfach/muellfach.de/{mailbox_name}"

        live_tracker.set_step(
            step=2,
            step_title="Filling Registration Form (Email & Password)",
            url="https://www.morelogin.com/register",
            active_tab="morelogin",
            email=email,
            password=password,
            mailbox_url=mailbox_url,
            log_msg=f"Generated mailbox: {email} | Filling form inputs..."
        )
        await update_status(f"🔐 [2/4] ইমেইল ও পাসওয়ার্ড পূরণ করা হচ্ছে...\n📧 ইমেইল: `{email}`")
        await asyncio.sleep(0.8)

        # Step 3: Submit Registration Request
        live_tracker.set_step(
            step=3,
            step_title="Submitting Registration to Gateway",
            url="https://www.morelogin.com/register",
            active_tab="morelogin",
            email=email,
            password=password,
            mailbox_url=mailbox_url,
            log_msg="Encrypting credentials & sending POST /app/user/register/home"
        )
        await update_status(f"🚀 [3/4] MoreLogin-এ রেজিস্ট্রেশন রিকোয়েস্ট পাঠানো হচ্ছে...")

        reg_success, reg_msg, reg_data = await loop.run_in_executor(
            None, self.register_on_morelogin, session, email, password
        )

        if not reg_success:
            live_tracker.set_error(reg_msg)
            return {
                "success": False,
                "error": reg_msg,
                "email": email,
                "password": password,
                "mailbox_url": mailbox_url
            }

        # Step 4: Switch to Müllfach.de Tab & Poll for Email
        live_tracker.set_step(
            step=4,
            step_title="Switching to Müllfach Inbox & Waiting for Email",
            url=mailbox_url,
            active_tab="muellfach",
            email=email,
            password=password,
            mailbox_url=mailbox_url,
            log_msg=f"Switched browser tab to {mailbox_url}. Listening for incoming mail..."
        )
        await update_status("📩 [4/4] এক্টিভেশন ইমেইল অপেক্ষা করা হচ্ছে (muellfach.de)...")

        act_link = await loop.run_in_executor(
            None, self.poll_for_activation_link, session, email, 45, 3
        )

        if not act_link:
            live_tracker.set_error("Activation email timeout")
            return {
                "success": False,
                "error": "Activation email timed out. Check mailbox manually.",
                "email": email,
                "password": password,
                "mailbox_url": mailbox_url
            }

        # Step 5: Click Activation
        live_tracker.set_step(
            step=5,
            step_title="Clicking 'Activate account' in Email",
            url=act_link,
            active_tab="muellfach",
            email=email,
            password=password,
            mailbox_url=mailbox_url,
            log_msg="Extracted activation token! Clicking activation link..."
        )

        activated = await loop.run_in_executor(
            None, self.activate_account, session, act_link
        )

        # Finished!
        live_tracker.set_success(email, password, mailbox_url)

        return {
            "success": True,
            "email": email,
            "password": password,
            "activated": activated,
            "activation_link": act_link,
            "mailbox_url": mailbox_url,
            "message": "Account successfully created and activated!"
        }
