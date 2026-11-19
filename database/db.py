import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from config import DB_PATH, DEFAULT_PASSWORD, DEFAULT_EMAIL_PREFIX
from core.password_gen import generate_strong_password

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0,
                live_alerts_enabled INTEGER DEFAULT 1
            )
            """)

            # User Settings table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                custom_password TEXT,
                password_type TEXT DEFAULT 'random',
                password_set_at TIMESTAMP,
                password_expires_at TIMESTAMP,
                email_prefix TEXT DEFAULT 'priyaahmed210208',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # Created Accounts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                is_activated INTEGER DEFAULT 1,
                activation_link TEXT,
                ip_address TEXT DEFAULT '',
                country TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # Migrations for existing tables
            try:
                cursor.execute("ALTER TABLE accounts ADD COLUMN ip_address TEXT DEFAULT ''")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE accounts ADD COLUMN country TEXT DEFAULT ''")
            except Exception:
                pass

            # Activity Logs table (Real-time tracking)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                button_name TEXT,
                action_type TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Support tickets table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                message TEXT,
                admin_reply TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                replied_at TIMESTAMP
            )
            """)

            conn.commit()

    # ── User Management ──────────────────────────────
    def register_or_update_user(self, user_id: int, username: Optional[str], first_name: Optional[str]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
            """, (user_id, username or "", first_name or ""))

            cursor.execute("""
            INSERT OR IGNORE INTO user_settings (user_id, custom_password, password_type, email_prefix)
            VALUES (?, ?, 'random', ?)
            """, (user_id, DEFAULT_PASSWORD, DEFAULT_EMAIL_PREFIX))
            conn.commit()

    def is_user_banned(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return bool(row and row["is_banned"])

    def set_user_ban_status(self, user_id: int, is_banned: bool):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (1 if is_banned else 0, user_id))
            conn.commit()

    # ── Password & User Settings ──────────────────────────────
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {
                "user_id": user_id,
                "custom_password": DEFAULT_PASSWORD,
                "password_type": "random",
                "password_set_at": None,
                "password_expires_at": None,
                "email_prefix": DEFAULT_EMAIL_PREFIX
            }

    def get_effective_password(self, user_id: int) -> Tuple[str, str]:
        settings = self.get_user_settings(user_id)
        p_type = settings.get("password_type", "random")
        custom_pwd = settings.get("custom_password")
        expires_at_str = settings.get("password_expires_at")

        if p_type == "24h":
            if expires_at_str:
                try:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    if datetime.now() > expires_at:
                        self.set_password_mode(user_id, "random")
                        new_pwd = generate_strong_password()
                        return new_pwd, "র‍্যান্ডম (২৪ ঘন্টা শেষ হওয়ায় অটো র‍্যান্ডম)"
                except Exception:
                    pass
            return custom_pwd or DEFAULT_PASSWORD, "২৪ ঘন্টার কাস্টম পাসওয়ার্ড"

        elif p_type == "permanent":
            return custom_pwd or DEFAULT_PASSWORD, "স্থায়ী (Permanent) পাসওয়ার্ড"

        else:
            return generate_strong_password(), "র‍্যান্ডম স্ট্রং পাসওয়ার্ড"

    def set_user_password(self, user_id: int, password: str, password_type: str):
        now = datetime.now()
        expires_at = None
        if password_type == "24h":
            expires_at = (now + timedelta(hours=24)).isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO user_settings (user_id, custom_password, password_type, password_set_at, password_expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                custom_password = excluded.custom_password,
                password_type = excluded.password_type,
                password_set_at = excluded.password_set_at,
                password_expires_at = excluded.password_expires_at
            """, (user_id, password, password_type, now.isoformat(), expires_at))
            conn.commit()

    def set_password_mode(self, user_id: int, password_type: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE user_settings
            SET password_type = ?, password_expires_at = NULL
            WHERE user_id = ?
            """, (password_type, user_id))
            conn.commit()

    def set_user_email_prefix(self, user_id: int, prefix: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE user_settings SET email_prefix = ? WHERE user_id = ?
            """, (prefix, user_id))
            conn.commit()

    # ── Accounts History ──────────────────────────────
    def save_account(self, user_id: int, email: str, password: str, is_activated: bool = True,
                     activation_link: str = "", ip_address: str = "", country: str = ""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO accounts (user_id, email, password, is_activated, activation_link, ip_address, country)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, email, password, 1 if is_activated else 0, activation_link, ip_address, country))
            conn.commit()

    def get_user_accounts(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM accounts WHERE user_id = ? ORDER BY id DESC LIMIT ?
            """, (user_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def get_user_account_count(self, user_id: int) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM accounts WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row["cnt"] if row else 0

    # ── Realtime Activity Tracking ──────────────────────────────
    def log_activity(self, user_id: int, username: Optional[str], full_name: Optional[str],
                     button_name: str, action_type: str, details: str = ""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO activity_logs (user_id, username, full_name, button_name, action_type, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username or "", full_name or "", button_name, action_type, details))
            conn.commit()

    def get_recent_activities(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_user_activities(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM activity_logs WHERE user_id = ? ORDER BY id DESC LIMIT ?
            """, (user_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    # ── Support System ──────────────────────────────
    def create_support_ticket(self, user_id: int, username: Optional[str], message: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO support_messages (user_id, username, message)
            VALUES (?, ?, ?)
            """, (user_id, username or "", message))
            conn.commit()
            return cursor.lastrowid

    def reply_support_ticket(self, ticket_id: int, reply_text: str) -> Optional[int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM support_messages WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            if not row:
                return None
            user_id = row["user_id"]
            cursor.execute("""
            UPDATE support_messages
            SET admin_reply = ?, status = 'replied', replied_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """, (reply_text, ticket_id))
            conn.commit()
            return user_id

    def get_pending_support_tickets(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM support_messages WHERE status = 'pending' ORDER BY id DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

    # ── Admin Stats ──────────────────────────────
    def get_system_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()["total_users"]

            cursor.execute("SELECT COUNT(*) as total_accounts FROM accounts")
            total_accounts = cursor.fetchone()["total_accounts"]

            cursor.execute("SELECT COUNT(*) as today_accounts FROM accounts WHERE date(created_at) = date('now')")
            today_accounts = cursor.fetchone()["today_accounts"]

            cursor.execute("SELECT COUNT(*) as today_clicks FROM activity_logs WHERE date(timestamp) = date('now')")
            today_clicks = cursor.fetchone()["today_clicks"]

            cursor.execute("SELECT COUNT(*) as pending_support FROM support_messages WHERE status = 'pending'")
            pending_support = cursor.fetchone()["pending_support"]

            return {
                "total_users": total_users,
                "total_accounts": total_accounts,
                "today_accounts": today_accounts,
                "today_clicks": today_clicks,
                "pending_support": pending_support
            }

    def get_all_user_ids(self) -> List[int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
            return [r["user_id"] for r in cursor.fetchall()]

    def toggle_admin_live_alerts(self, admin_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT live_alerts_enabled FROM users WHERE user_id = ?", (admin_id,))
            row = cursor.fetchone()
            current = row["live_alerts_enabled"] if row else 1
            new_val = 0 if current else 1
            cursor.execute("UPDATE users SET live_alerts_enabled = ? WHERE user_id = ?", (new_val, admin_id))
            conn.commit()
            return bool(new_val)

    def is_live_alerts_enabled(self, admin_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT live_alerts_enabled FROM users WHERE user_id = ?", (admin_id,))
            row = cursor.fetchone()
            if row is not None and row["live_alerts_enabled"] is not None:
                return bool(row["live_alerts_enabled"])
            return True
