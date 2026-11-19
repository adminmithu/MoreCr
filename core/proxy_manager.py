import os
import re
import random
import requests
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from config import BASE_DIR

PROXIES_FILE = BASE_DIR / "proxies.txt"

def get_flag_emoji(country_code: str) -> str:
    """Converts 2-letter country code (e.g. 'US', 'BD') to flag emoji"""
    if not country_code or len(country_code) != 2:
        return "🌐"
    try:
        return "".join(chr(ord(c.upper()) + 127397) for c in country_code)
    except Exception:
        return "🌐"

class ProxyManager:
    def __init__(self, file_path: Path = PROXIES_FILE):
        self.file_path = file_path
        self.proxies: List[str] = []
        self.current_index = 0
        self.is_enabled = True
        self.load_proxies()

    def parse_proxy(self, proxy_str: str) -> Optional[str]:
        """
        Parses various proxy formats into standard URL:
        - ip:port -> http://ip:port
        - ip:port:user:pass -> http://user:pass@ip:port
        - user:pass@ip:port -> http://user:pass@ip:port
        - http://... or socks5://... -> as is
        """
        raw = proxy_str.strip()
        if not raw or raw.startswith("#"):
            return None

        # Already has protocol
        if raw.startswith(("http://", "https://", "socks5://", "socks4://")):
            return raw

        parts = raw.split(":")
        # Format: ip:port
        if len(parts) == 2:
            ip, port = parts
            return f"http://{ip}:{port}"

        # Format: ip:port:user:pass
        elif len(parts) == 4:
            ip, port, user, pwd = parts
            return f"http://{user}:{pwd}@{ip}:{port}"

        # Format: user:pass@ip:port
        elif "@" in raw:
            return f"http://{raw}"

        return f"http://{raw}"

    def load_proxies(self) -> int:
        """Loads and parses proxies from file"""
        if not self.file_path.exists():
            # Create default empty template
            template = (
                "# Paste your proxies below (one per line)\n"
                "# Supported formats:\n"
                "#   ip:port\n"
                "#   ip:port:username:password\n"
                "#   http://username:password@ip:port\n"
                "#   socks5://username:password@ip:port\n\n"
            )
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(template)
            self.proxies = []
            return 0

        loaded = []
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parsed = self.parse_proxy(line)
                    if parsed:
                        loaded.append(parsed)
            self.proxies = loaded
        except Exception:
            self.proxies = []

        return len(self.proxies)

    def save_proxies(self, proxy_list: List[str]):
        """Saves proxy list to file"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("# MoreLogin Creator Proxy List\n")
            for p in proxy_list:
                clean = p.strip()
                if clean:
                    f.write(clean + "\n")
        self.load_proxies()

    def add_proxies(self, new_lines: List[str]) -> int:
        """Appends new proxies to file and reloads"""
        added = 0
        with open(self.file_path, "a", encoding="utf-8") as f:
            for line in new_lines:
                clean = line.strip()
                if clean and not clean.startswith("#"):
                    f.write("\n" + clean)
                    added += 1
        self.load_proxies()
        return added

    def toggle_mode(self) -> bool:
        """Toggles proxy mode ON/OFF"""
        self.is_enabled = not self.is_enabled
        return self.is_enabled

    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Gets next proxy dict in round-robin fashion.
        Returns dict formatted for `requests`: {'http': url, 'https': url, 'raw': url}
        """
        if not self.is_enabled or not self.proxies:
            return None

        # Rotate index
        proxy_url = self.proxies[self.current_index % len(self.proxies)]
        self.current_index = (self.current_index + 1) % len(self.proxies)

        return {
            "http": proxy_url,
            "https": proxy_url,
            "raw": proxy_url
        }

    @staticmethod
    def check_ip(proxies: Optional[Dict[str, str]] = None, timeout: int = 8) -> Tuple[bool, str, str, str]:
        """
        Checks current public IP and location (via proxy or direct).
        Returns: (success: bool, ip: str, country_name: str, country_code: str)
        """
        req_proxies = None
        if proxies and "http" in proxies and "https" in proxies:
            req_proxies = {
                "http": proxies["http"],
                "https": proxies["https"]
            }

        try:
            # First try ip-api (fast, gives country info)
            resp = requests.get(
                "http://ip-api.com/json/?fields=status,query,country,countryCode,city",
                proxies=req_proxies,
                timeout=timeout
            )
            data = resp.json()
            if data.get("status") == "success" or "query" in data:
                ip = data.get("query", "")
                country = data.get("country", "Unknown")
                code = data.get("countryCode", "")
                return True, ip, country, code
        except Exception:
            pass

        # Fallback to ipify
        try:
            resp = requests.get(
                "https://api.ipify.org?format=json",
                proxies=req_proxies,
                timeout=timeout
            )
            data = resp.json()
            ip = data.get("ip", "")
            if ip:
                return True, ip, "Direct", ""
        except Exception:
            pass

        return False, "Unknown", "Unknown", ""

    def get_status(self) -> Dict[str, Any]:
        """Returns proxy manager status for dashboard & admin bot"""
        return {
            "enabled": self.is_enabled,
            "total_proxies": len(self.proxies),
            "current_index": self.current_index,
            "has_proxies": len(self.proxies) > 0
        }

# Global instance
proxy_manager = ProxyManager()
