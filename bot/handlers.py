import html
import io
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, is_admin, DEFAULT_EMAIL_PREFIX
from database.db import Database
from core.morelogin import MoreLoginCreator
from core.password_gen import validate_password, generate_strong_password
from bot.keyboards import (
    get_main_keyboard,
    get_password_menu_keyboard,
    get_cancel_keyboard,
    get_history_keyboard,
    get_admin_keyboard,
    BTN_CREATE_ACCOUNT,
    BTN_SET_PASSWORD,
    BTN_HISTORY,
    BTN_SUPPORT,
    BTN_ADMIN_PANEL,
    BTN_PWD_PERMANENT,
    BTN_PWD_24H,
    BTN_PWD_RANDOM,
    BTN_HIST_COPY,
    BTN_HIST_EXPORT,
    BTN_ADM_LIVE,
    BTN_ADM_ALERTS,
    BTN_ADM_STATS,
    BTN_ADM_USERS,
    BTN_ADM_SUPPORT,
    BTN_ADM_BROADCAST,
    BTN_BACK_MAIN,
    BTN_CANCEL
)
from bot.admin import (
    notify_admins_activity,
    show_admin_panel,
    toggle_live_alerts,
    show_live_feed,
    show_system_stats,
    show_user_list,
    show_support_inbox,
    start_broadcast_prompt
)

db = Database()
creator = MoreLoginCreator()

async def log_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE, button_name: str, action_type: str, details: str = ""):
    """Helper to log user actions and push real-time alerts to admins"""
    user = update.effective_user
    if not user:
        return
    db.log_activity(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        button_name=button_name,
        action_type=action_type,
        details=details
    )
    await notify_admins_activity(
        bot=context.bot,
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name or "User",
        button_name=button_name,
        action_type=action_type,
        details=details
    )

# ── /start Handler ──────────────────────────────────────────
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data.clear()
    db.register_or_update_user(user.id, user.username, user.full_name)

    await log_and_notify(update, context, "/start", "command", "User opened main menu")

    welcome_text = (
        f"👋 <b>স্বাগতম, {html.escape(user.first_name)}!</b>\n\n"
        f"🤖 <b>MoreLogin একাউন্ট ক্রিয়েটর অটোমেশন বট</b>\n"
        f"এখানে আপনি মাত্র <b>১-ক্লিকে</b> স্বয়ংক্রিয়ভাবে MoreLogin Antidetect Browser এর সম্পূর্ণ এক্টিভেটেড ও প্রস্তুত একাউন্ট তৈরি করতে পারবেন।\n\n"
        f"⚡ <b>ফিচারসমূহ:</b>\n"
        f"• <b>১-ক্লিক একাউন্ট ক্রিয়েশন:</b> muellfach.de থেকে অটো ইমেইল ভেরিফিকেশন ও ইনস্ট্যান্ট এক্টিভেশন।\n"
        f"• <b>কাস্টম পাসওয়ার্ড:</b> স্থায়ী বা ২৪ ঘন্টার জন্য কাস্টম পাসওয়ার্ড সেট করার সুবিধা।\n"
        f"• <b>হিস্ট্রি সংরক্ষণ:</b> আপনার তৈরিকৃত একাউন্টের তালিকা ও TXT এক্সপোর্ট।\n"
        f"• <b>সরাসরি অ্যাডমিন সাপোর্ট:</b> যেকোনো সমস্যা লিখে পাঠালেই সরাসরি অ্যাডমিনের কাছে পৌঁছাবে।\n\n"
        f"👇 <i>নিচের কিবোর্ড বাটনগুলো চেপে অপশন সিলেক্ট করুন:</i>"
    )

    is_adm = is_admin(user.id)
    await update.message.reply_text(
        text=welcome_text,
        reply_markup=get_main_keyboard(is_adm),
        parse_mode="HTML"
    )

# ── Main ReplyKeyboard & Text Message Router ────────────────
async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg_text = update.message.text.strip()
    is_adm = is_admin(user.id)

    if db.is_user_banned(user.id):
        await update.message.reply_text("❌ আপনার একাউন্টটি সাময়িকভাবে নিষিদ্ধ করা হয়েছে।")
        return

    # 1. Back to Main Menu or Cancel
    if msg_text in (BTN_BACK_MAIN, BTN_CANCEL):
        context.user_data.clear()
        await log_and_notify(update, context, msg_text, "click_button", "Returned to main menu")
        await update.message.reply_text(
            "🏠 <b>প্রধান মেনু:</b>\nনিচের বাটন চেপে আপনার প্রয়োজনীয় অপশন সিলেক্ট করুন।",
            reply_markup=get_main_keyboard(is_adm),
            parse_mode="HTML"
        )
        return

    # 2. 1-Click Create Account Button
    if msg_text == BTN_CREATE_ACCOUNT:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_CREATE_ACCOUNT, "click_button", "Initiated 1-click create")
        await process_create_account(update, context)
        return

    # 3. Password Menu Button
    if msg_text == BTN_SET_PASSWORD:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_SET_PASSWORD, "click_button", "Opened password settings")
        await show_password_menu(update, context)
        return

    # 4. Password Options
    if msg_text == BTN_PWD_PERMANENT:
        context.user_data["awaiting_password_type"] = "permanent"
        await log_and_notify(update, context, BTN_PWD_PERMANENT, "click_button", "Selected permanent password option")
        await update.message.reply_text(
            "📌 <b>স্থায়ী (Permanent) পাসওয়ার্ড সেট করুন</b>\n\n"
            "আপনার কাঙ্ক্ষিত পাসওয়ার্ডটি লিখে মেসেজ পাঠান।\n"
            "<i>(শর্ত: ন্যূনতম ৮ অক্ষরের হতে হবে এবং অক্ষর ও সংখ্যা মিলিয়ে লিখতে হবে)</i>\n\n"
            "বাতিল করতে নিচের <b>❌ বাতিল</b> বাটন চাপুন।",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    elif msg_text == BTN_PWD_24H:
        context.user_data["awaiting_password_type"] = "24h"
        await log_and_notify(update, context, BTN_PWD_24H, "click_button", "Selected 24h password option")
        await update.message.reply_text(
            "⏳ <b>২৪ ঘন্টার জন্য পাসওয়ার্ড সেট করুন</b>\n\n"
            "আপনার কাঙ্ক্ষিত পাসওয়ার্ডটি লিখে মেসেজ পাঠান।\n"
            "<i>(শর্ত: ন্যূনতম ৮ অক্ষরের হতে হবে এবং অক্ষর ও সংখ্যা মিলিয়ে লিখতে হবে)</i>\n\n"
            "এই পাসওয়ার্ডটি আগামী <b>২৪ ঘন্টা</b> পর্যন্ত কার্যকর থাকবে। তারপর অটোমেটিকভাবে র‍্যান্ডম পাসওয়ার্ডে ফিরে যাবে।\n\n"
            "বাতিল করতে নিচের <b>❌ বাতিল</b> বাটন চাপুন।",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    elif msg_text == BTN_PWD_RANDOM:
        context.user_data.clear()
        db.set_password_mode(user.id, "random")
        await log_and_notify(update, context, BTN_PWD_RANDOM, "click_button", "Set password to auto-random")
        await update.message.reply_text(
            "✅ <b>অটো র‍্যান্ডম পাসওয়ার্ড মোড চালু করা হয়েছে!</b>\n"
            "এখন প্রতিবারে একাউন্ট তৈরির সময় স্বয়ংক্রিয়ভাবে ইউনিক শক্তিশালী পাসওয়ার্ড তৈরি হবে।",
            reply_markup=get_main_keyboard(is_adm),
            parse_mode="HTML"
        )
        return

    # 5. History Button
    if msg_text == BTN_HISTORY:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_HISTORY, "click_button", "Opened history")
        await show_history(update, context)
        return

    if msg_text == BTN_HIST_COPY:
        await log_and_notify(update, context, BTN_HIST_COPY, "click_button", "Requested email:pass format")
        await show_history_copy_format(update, context)
        return

    elif msg_text == BTN_HIST_EXPORT:
        await log_and_notify(update, context, BTN_HIST_EXPORT, "click_button", "Downloaded history TXT file")
        await export_history_txt(update, context)
        return

    # 6. Support Button
    if msg_text == BTN_SUPPORT:
        context.user_data["awaiting_support"] = True
        await log_and_notify(update, context, BTN_SUPPORT, "click_button", "Opened support dialogue")
        await update.message.reply_text(
            "💬 <b>অ্যাডমিন সাপোর্ট (Contact Admin)</b>\n\n"
            "আপনার কোনো সমস্যা, অভিযোগ বা জিজ্ঞাসা থাকলে সরাসরি মেসেজ লিখে পাঠান।\n"
            "আপনার মেসেজটি সরাসরি অ্যাডমিনের কাছে চলে যাবে এবং অ্যাডমিন দ্রুত আপনাকে উত্তর দেবেন।\n\n"
            "বাতিল করতে চাইলে নিচের <b>❌ বাতিল</b> বাটনে চাপ দিন।",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    # 7. Admin Panel Buttons
    if msg_text == BTN_ADMIN_PANEL and is_adm:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_ADMIN_PANEL, "click_button", "Admin opened control panel")
        await show_admin_panel(update, context)
        return

    if is_adm:
        if msg_text == BTN_ADM_LIVE:
            await log_and_notify(update, context, BTN_ADM_LIVE, "click_button", "Viewed live feed")
            await show_live_feed(update, context)
            return
        elif msg_text == BTN_ADM_ALERTS:
            await toggle_live_alerts(update, context)
            return
        elif msg_text == BTN_ADM_STATS:
            await show_system_stats(update, context)
            return
        elif msg_text == BTN_ADM_USERS:
            await show_user_list(update, context)
            return
        elif msg_text == BTN_ADM_SUPPORT:
            await show_support_inbox(update, context)
            return
        elif msg_text == BTN_ADM_BROADCAST:
            await start_broadcast_prompt(update, context)
            return

    # ────────────────────────────────────────────────────────
    # 8. State Processing: Input handlers
    # ────────────────────────────────────────────────────────

    # A. Setting Password
    pwd_type = context.user_data.get("awaiting_password_type")
    if pwd_type in ("permanent", "24h"):
        is_valid, err_msg = validate_password(msg_text)
        if not is_valid:
            await update.message.reply_text(
                f"❌ <b>পাসওয়ার্ড গ্রহণযোগ্য নয়!</b>\n\n{err_msg}\nঅনুগ্রহ করে আবার লিখে পাঠান (বা বাতিল করতে ❌ বাতিল চাপুন):",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML"
            )
            return

        db.set_user_password(user.id, msg_text, pwd_type)
        context.user_data.pop("awaiting_password_type", None)

        mode_name = "স্থায়ী (Permanent)" if pwd_type == "permanent" else "২৪ ঘন্টার জন্য"
        await log_and_notify(
            update, context,
            button_name=f"Set Password ({pwd_type})",
            action_type="set_password",
            details=f"Set password: {msg_text}"
        )

        await update.message.reply_text(
            f"✅ <b>পাসওয়ার্ড সফলভাবে সংরক্ষিত হয়েছে!</b>\n\n"
            f"🔐 আপনার নতুন পাসওয়ার্ড: <code>{html.escape(msg_text)}</code>\n"
            f"🛡️ ধরণ: <b>{mode_name}</b>\n\n"
            f"এখন একাউন্ট তৈরি করলে এই পাসওয়ার্ডটি ব্যবহার করা হবে।",
            reply_markup=get_main_keyboard(is_adm),
            parse_mode="HTML"
        )
        return

    # B. Admin Broadcast State
    if context.user_data.get("awaiting_broadcast") and is_adm:
        context.user_data.pop("awaiting_broadcast", None)
        user_ids = db.get_all_user_ids()
        sent_count = 0
        for uid in user_ids:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"📢 <b>অ্যাডমিন বার্তা (Admin Announcement):</b>\n\n{html.escape(msg_text)}",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception:
                pass

        await update.message.reply_text(
            f"✅ <b>ব্রডকাস্ট সম্পন্ন হয়েছে!</b>\nমোট <b>{sent_count}</b> জন ইউজারের কাছে বার্তা পৌঁছেছে।",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        return

    # C. Direct Support Message
    context.user_data.pop("awaiting_support", None)
    ticket_id = db.create_support_ticket(user.id, user.username, msg_text)

    await log_and_notify(
        update, context,
        button_name="সাপোর্ট মেসেজ",
        action_type="support_message",
        details=f"Ticket #{ticket_id}: {msg_text}"
    )

    uname_str = f"@{user.username}" if user.username else f"ID: {user.id}"
    admin_alert = (
        f"📩 <b>[নতুন সাপোর্ট মেসেজ - টিকেট #{ticket_id}]</b>\n"
        f"👤 প্রেরক: <b>{html.escape(user.full_name)}</b> ({uname_str})\n"
        f"🆔 ইউজার আইডি: <code>{user.id}</code>\n"
        f"⏰ সময়: <code>{datetime.now().strftime('%Y-%m-%d %I:%M %p')}</code>\n\n"
        f"💬 <b>মেসেজ:</b>\n"
        f"<i>{html.escape(msg_text)}</i>\n\n"
        f"👉 উত্তর দিতে টাইপ করুন: <code>/reply {ticket_id} আপনার বার্তা</code>"
    )

    for aid in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=aid,
                text=admin_alert,
                parse_mode="HTML"
            )
        except Exception:
            pass

    await update.message.reply_text(
        "✅ <b>আপনার মেসেজটি অ্যাডমিনের কাছে সফলভাবে পৌঁছেছে!</b>\n"
        "অ্যাডমিন মেসেজটি দেখে শীঘ্রই আপনার সাথে যোগাযোগ করবেন। ধন্যবাদ!",
        reply_markup=get_main_keyboard(is_adm),
        parse_mode="HTML"
    )

# ── Account Creation Logic ────────────────────────────────────
async def process_create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_adm = is_admin(user.id)

    status_msg = await update.message.reply_text(
        "⚡ <b>১-ক্লিক একাউন্ট তৈরির প্রক্রিয়া শুরু হয়েছে...</b>\nঅনুগ্রহ করে অপেক্ষা করুন...",
        parse_mode="HTML"
    )

    async def progress_update(step_text: str):
        try:
            await status_msg.edit_text(
                text=f"⚡ <b>MoreLogin একাউন্ট তৈরি হচ্ছে...</b>\n\n{step_text}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Retrieve password
    password, pwd_type_desc = db.get_effective_password(user.id)
    settings = db.get_user_settings(user.id)
    email_prefix = settings.get("email_prefix") or DEFAULT_EMAIL_PREFIX

    # Run flow
    result = await creator.create_account_full_flow(
        email_prefix=email_prefix,
        password=password,
        progress_callback=progress_update
    )

    if result.get("success"):
        email = result["email"]
        mailbox_url = result["mailbox_url"]
        act_link = result.get("activation_link", "")

        # Save to database
        db.save_account(
            user_id=user.id,
            email=email,
            password=password,
            is_activated=True,
            activation_link=act_link
        )

        db.log_activity(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            button_name="Account Created",
            action_type="create_account",
            details=f"Created {email}"
        )

        # Notify admins
        await notify_admins_activity(
            bot=context.bot,
            user_id=user.id,
            username=user.username or "",
            full_name=user.full_name or "User",
            button_name="✅ একাউন্ট সম্পন্ন",
            action_type="account_success",
            details=f"Email: {email} | Pass: {password}"
        )

        success_text = (
            f"🎉 <b>অভিনন্দন! আপনার MoreLogin একাউন্ট প্রস্তুত!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📧 <b>ইমেইল:</b> <code>{email}</code>\n"
            f"🔑 <b>পাসওয়ার্ড:</b> <code>{password}</code>\n"
            f"🛡️ <b>পাসওয়ার্ড ধরণ:</b> {pwd_type_desc}\n"
            f"✅ <b>স্ট্যাটাস:</b> সম্পূর্ণ এক্টিভেটেড ও ভেরিফাইড\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📬 <b>মেইলবক্স লিঙ্ক:</b> <a href=\"{mailbox_url}\">ইনবক্স দেখুন (muellfach.de)</a>\n\n"
            f"💡 <i>(ইমেইল বা পাসওয়ার্ডের উপর চাপ দিলে সাথে সাথে কপি হবে)</i>"
        )

        await status_msg.edit_text(
            text=success_text,
            reply_markup=None,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        await update.message.reply_text(
            "👇 <i>আরেকটি একাউন্ট তৈরি করতে নিচের '⚡ 1-Click একাউন্ট তৈরি' বাটন চাপুন:</i>",
            reply_markup=get_main_keyboard(is_adm),
            parse_mode="HTML"
        )

    else:
        err = result.get("error", "Unknown error")
        db.log_activity(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            button_name="Account Creation Failed",
            action_type="error",
            details=f"Failed: {err}"
        )
        fail_text = (
            f"❌ <b>একাউন্ট তৈরিতে সমস্যা হয়েছে!</b>\n\n"
            f"⚠️ কারণ: <code>{html.escape(err)}</code>\n\n"
            f"অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন অথবা সাপোর্টে যোগাযোগ করুন।"
        )
        await status_msg.edit_text(
            text=fail_text,
            parse_mode="HTML"
        )
        await update.message.reply_text(
            "পুনরায় চেষ্টা করতে নিচের বাটন ব্যবহার করুন:",
            reply_markup=get_main_keyboard(is_adm)
        )

# ── Password Menu Logic ────────────────────────────────────
async def show_password_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    settings = db.get_user_settings(user.id)
    p_type = settings.get("password_type", "random")
    current_pwd = settings.get("custom_password") or "সেট করা নেই"
    expires_at_str = settings.get("password_expires_at")

    if p_type == "permanent":
        type_str = "📌 স্থায়ী (Permanent)"
    elif p_type == "24h":
        rem = ""
        if expires_at_str:
            try:
                exp = datetime.fromisoformat(expires_at_str)
                delta = exp - datetime.now()
                if delta.total_seconds() > 0:
                    hours, rem_sec = divmod(int(delta.total_seconds()), 3600)
                    mins = rem_sec // 60
                    rem = f" (বাকি {hours} ঘন্টা {mins} মিনিট)"
                else:
                    rem = " (মেয়াদ শেষ)"
            except Exception:
                pass
        type_str = f"⏳ ২৪ ঘন্টা{rem}"
    else:
        type_str = "🎲 অটো র‍্যান্ডম (প্রতিবারে শক্তিশালী ইউনিক পাসওয়ার্ড)"

    text = (
        f"🔑 <b>পাসওয়ার্ড সেটিংস ও ম্যানেজমেন্ট</b>\n\n"
        f"🛡️ বর্তমান পাসওয়ার্ড মোড: <b>{type_str}</b>\n"
        f"🔐 কাস্টম পাসওয়ার্ড: <code>{html.escape(current_pwd)}</code>\n\n"
        f"<i>নিচের বাটনগুলোর মাধ্যমে আপনার পছন্দ নির্বাচন করুন:</i>\n\n"
        f"• <b>স্থায়ী পাসওয়ার্ড:</b> সবসময় আপনার দেওয়া পাসওয়ার্ডে একাউন্ট তৈরি হবে।\n"
        f"• <b>২৪ ঘন্টার পাসওয়ার্ড:</b> আগামী ২৪ ঘন্টার জন্য সাময়িক পাসওয়ার্ড থাকবে।\n"
        f"• <b>অটো র‍্যান্ডম:</b> প্রতিবার স্বয়ংক্রিয়ভাবে নতুন সিকিউর পাসওয়ার্ড তৈরি হবে।"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=get_password_menu_keyboard(),
        parse_mode="HTML"
    )

# ── History Logic ──────────────────────────────────────────
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_adm = is_admin(user.id)

    accounts = db.get_user_accounts(user.id, limit=8)
    total_count = db.get_user_account_count(user.id)

    if not accounts:
        text = (
            f"📜 <b>আপনার তৈরিকৃত একাউন্ট হিস্ট্রি</b>\n\n"
            f"⚠️ আপনি এখনও কোনো MoreLogin একাউন্ট তৈরি করেননি।\n"
            f"একাউন্ট তৈরি করতে নিচের <b>⚡ 1-Click একাউন্ট তৈরি</b> বাটন চাপুন।"
        )
        await update.message.reply_text(
            text=text,
            reply_markup=get_history_keyboard(has_accounts=False),
            parse_mode="HTML"
        )
        return

    text = f"📜 <b>আপনার একাউন্ট হিস্ট্রি (মোট {total_count} টি):</b>\n\n"
    for i, acc in enumerate(accounts, 1):
        dt = acc['created_at'].split()[0] if ' ' in acc['created_at'] else acc['created_at']
        text += (
            f"<b>{i}.</b> 📧 <code>{acc['email']}</code>\n"
            f"   🔑 <code>{acc['password']}</code>\n"
            f"   📅 <i>{dt}</i> | ✅ এক্টিভেটেড\n\n"
        )

    text += "💡 <i>সবগুলো একসাথে কপি করতে বা TXT ফাইল ডাউনলোড করতে নিচের বাটন চাপুন:</i>"

    await update.message.reply_text(
        text=text,
        reply_markup=get_history_keyboard(has_accounts=True),
        parse_mode="HTML"
    )

async def show_history_copy_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    accounts = db.get_user_accounts(user.id, limit=50)
    if not accounts:
        await update.message.reply_text("কোনো হিস্ট্রি পাওয়া যায়নি।", reply_markup=get_history_keyboard(False))
        return

    copy_lines = [f"{acc['email']}:{acc['password']}" for acc in accounts]
    joined = "\n".join(copy_lines)

    text = (
        f"📋 <b>কপি ফরম্যাট (email:pass):</b>\n\n"
        f"<code>{joined}</code>\n\n"
        f"👆 <i>উপরে কোড ব্লকে চাপ দিলে সব একসাথে কপি হয়ে যাবে।</i>"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=get_history_keyboard(True),
        parse_mode="HTML"
    )

async def export_history_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    accounts = db.get_user_accounts(user.id, limit=200)

    if not accounts:
        await update.message.reply_text("কোনো হিস্ট্রি পাওয়া যায়নি।")
        return

    lines = [f"{acc['email']}:{acc['password']}" for acc in accounts]
    content = "\n".join(lines)

    bio = io.BytesIO(content.encode('utf-8'))
    bio.name = f"morelogin_accounts_{user.id}.txt"

    await context.bot.send_document(
        chat_id=user.id,
        document=bio,
        caption=f"📥 <b>আপনার মোট {len(accounts)} টি MoreLogin একাউন্টের তালিকা (email:password)</b>",
        reply_markup=get_history_keyboard(True),
        parse_mode="HTML"
    )

# ── Admin /reply command (/reply <ticket_id> <message>) ──────
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "ব্যবহারের নিয়ম: <code>/reply &lt;টিকেট_আইডি&gt; &lt;আপনার উত্তর&gt;</code>",
            parse_mode="HTML"
        )
        return

    try:
        ticket_id = int(context.args[0])
        reply_msg = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ টিকেট আইডি সংখ্যা হতে হবে।")
        return

    target_uid = db.reply_support_ticket(ticket_id, reply_msg)
    if not target_uid:
        await update.message.reply_text("❌ এই টিকেটটি পাওয়া যায়নি।")
        return

    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=(
                f"👨‍💻 <b>অ্যাডমিনের উত্তর (Admin Support Reply):</b>\n\n"
                f"💬 <i>{html.escape(reply_msg)}</i>\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"আরও কোনো প্রশ্ন থাকলে সরাসরি মেসেজ লিখে পাঠাতে পারেন।"
            ),
            parse_mode="HTML"
        )
        await update.message.reply_text(f"✅ টিকেট #{ticket_id} এর রিপ্লাই ইউজারের কাছে পাঠানো হয়েছে!")
    except Exception as e:
        await update.message.reply_text(f"❌ ইউজারকে মেসেজ পাঠাতে ব্যর্থ: {e}")
