import random
import string
import re

def generate_strong_password(length: int = 12) -> str:
    """
    Generates a secure, strong password compatible with MoreLogin requirements.
    At least 8 chars, uppercase, lowercase, digits, and special characters.
    """
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%"
    
    # Ensure at least one of each
    pwd_chars = [
        random.choice(upper),
        random.choice(lower),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Fill remainder
    all_chars = upper + lower + digits + special
    for _ in range(max(length - 4, 8)):
        pwd_chars.append(random.choice(all_chars))
        
    random.shuffle(pwd_chars)
    return "".join(pwd_chars)

def validate_password(pwd: str) -> tuple[bool, str]:
    """
    Validates if password meets MoreLogin criteria:
    Length >= 8 and at least 2 character types.
    """
    if not pwd or len(pwd) < 8:
        return False, "পাসওয়ার্ড ন্যূনতম ৮ অক্ষরের হতে হবে (Minimum 8 characters required)."
        
    types = 0
    if re.search(r'[A-Z]', pwd):
        types += 1
    if re.search(r'[a-z]', pwd):
        types += 1
    if re.search(r'[0-9]', pwd):
        types += 1
    if re.search(r'[^A-Za-z0-9]', pwd):
        types += 1
        
    if types < 2:
        return False, "পাসওয়ার্ডে অন্তত দুই ধরনের অক্ষর (যেমন অক্ষর ও সংখ্যা) থাকতে হবে।"
        
    return True, "Valid"
