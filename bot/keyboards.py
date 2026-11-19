from telegram import ReplyKeyboardMarkup, KeyboardButton

# Button Labels (Constants)
BTN_CREATE_ACCOUNT = "⚡ 1-Click একাউন্ট তৈরি"
BTN_SET_PASSWORD = "🔑 পাসওয়ার্ড সেট"
BTN_HISTORY = "📜 হিস্ট্রি"
BTN_SUPPORT = "💬 সাপোর্ট"
BTN_ADMIN_PANEL = "👑 অ্যাডমিন প্যানেল"

BTN_PWD_PERMANENT = "📌 স্থায়ী পাসওয়ার্ড"
BTN_PWD_24H = "⏳ ২৪ ঘন্টার পাসওয়ার্ড"
BTN_PWD_RANDOM = "🎲 অটো র‍্যান্ডম পাসওয়ার্ড"

BTN_HIST_COPY = "📋 কপি ফরম্যাট (email:pass)"
BTN_HIST_EXPORT = "📥 TXT ফাইল ডাউনলোড"

BTN_ADM_LIVE = "📡 লাইভ ক্লিক অ্যাক্টিভিটি"
BTN_ADM_ALERTS = "🔔 লাইভ পুশ অ্যালার্ট (Toggle)"
BTN_ADM_STATS = "📊 বট পরিসংখ্যান"
BTN_ADM_USERS = "👥 ইউজার লিস্ট"
BTN_ADM_SUPPORT = "📩 সাপোর্ট ইনবক্স"
BTN_ADM_BROADCAST = "📢 ব্রডকাস্ট নোটিশ"

BTN_BACK_MAIN = "🔙 প্রধান মেনু"
BTN_CANCEL = "❌ বাতিল"

def get_main_keyboard(is_admin_user: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_CREATE_ACCOUNT)],
        [KeyboardButton(BTN_SET_PASSWORD), KeyboardButton(BTN_HISTORY)],
        [KeyboardButton(BTN_SUPPORT)]
    ]
    if is_admin_user:
        keyboard.append([KeyboardButton(BTN_ADMIN_PANEL)])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_password_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_PWD_PERMANENT), KeyboardButton(BTN_PWD_24H)],
        [KeyboardButton(BTN_PWD_RANDOM)],
        [KeyboardButton(BTN_BACK_MAIN)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton(BTN_CANCEL)]], resize_keyboard=True)

def get_history_keyboard(has_accounts: bool = True) -> ReplyKeyboardMarkup:
    keyboard = []
    if has_accounts:
        keyboard.append([KeyboardButton(BTN_HIST_COPY), KeyboardButton(BTN_HIST_EXPORT)])
    keyboard.append([KeyboardButton(BTN_BACK_MAIN)])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(BTN_ADM_LIVE), KeyboardButton(BTN_ADM_ALERTS)],
        [KeyboardButton(BTN_ADM_STATS), KeyboardButton(BTN_ADM_USERS)],
        [KeyboardButton(BTN_ADM_SUPPORT), KeyboardButton(BTN_ADM_BROADCAST)],
        [KeyboardButton(BTN_BACK_MAIN)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
