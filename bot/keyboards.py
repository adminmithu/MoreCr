from telegram import ReplyKeyboardMarkup, KeyboardButton

# Button Labels (Clean English without dot emojis)
BTN_CREATE_ACCOUNT = "⚡ 1-Click Create Account"
BTN_SET_PASSWORD = "🔑 Set Password"
BTN_HISTORY = "📜 Account History"
BTN_SUPPORT = "💬 Contact Support"
BTN_ADMIN_PANEL = "👑 Admin Panel"

BTN_PWD_PERMANENT = "📌 Permanent Password"
BTN_PWD_24H = "⏳ 24-Hour Password"
BTN_PWD_RANDOM = "🎲 Auto Random Password"

BTN_HIST_COPY = "📋 Copy Format (email:pass)"
BTN_HIST_EXPORT = "📥 Download TXT File"

BTN_ADM_LIVE = "📡 Live Click Activity"
BTN_ADM_ALERTS = "🔔 Toggle Live Push Alerts"
BTN_ADM_STATS = "📊 Bot Analytics"
BTN_ADM_USERS = "👥 User List"
BTN_ADM_SUPPORT = "📩 Support Inbox"
BTN_ADM_BROADCAST = "📢 Broadcast Notice"

BTN_BACK_MAIN = "🔙 Main Menu"
BTN_CANCEL = "❌ Cancel"

def make_btn(text: str, style: str = "primary") -> KeyboardButton:
    """
    Creates a KeyboardButton styled using Telegram Bot API color properties:
    - 'success': Green
    - 'primary': Dark Blue / White
    - 'danger': Red
    """
    return KeyboardButton(text=text, api_kwargs={"style": style})

def get_main_keyboard(is_admin_user: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [make_btn(BTN_CREATE_ACCOUNT, style="success")],
        [make_btn(BTN_SET_PASSWORD, style="primary"), make_btn(BTN_HISTORY, style="primary")],
        [make_btn(BTN_SUPPORT, style="primary")]
    ]
    if is_admin_user:
        keyboard.append([make_btn(BTN_ADMIN_PANEL, style="danger")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_password_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [make_btn(BTN_PWD_PERMANENT, style="success"), make_btn(BTN_PWD_24H, style="primary")],
        [make_btn(BTN_PWD_RANDOM, style="primary")],
        [make_btn(BTN_BACK_MAIN, style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[make_btn(BTN_CANCEL, style="danger")]], resize_keyboard=True)

def get_history_keyboard(has_accounts: bool = True) -> ReplyKeyboardMarkup:
    keyboard = []
    if has_accounts:
        keyboard.append([make_btn(BTN_HIST_COPY, style="success"), make_btn(BTN_HIST_EXPORT, style="primary")])
    keyboard.append([make_btn(BTN_BACK_MAIN, style="danger")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [make_btn(BTN_ADM_LIVE, style="primary"), make_btn(BTN_ADM_ALERTS, style="success")],
        [make_btn(BTN_ADM_STATS, style="primary"), make_btn(BTN_ADM_USERS, style="primary")],
        [make_btn(BTN_ADM_SUPPORT, style="primary"), make_btn(BTN_ADM_BROADCAST, style="danger")],
        [make_btn(BTN_BACK_MAIN, style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
