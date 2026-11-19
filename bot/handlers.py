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
        f"👋 <b>Welcome, {html.escape(user.first_name)}!</b>\n\n"
        f"🤖 <b>MoreLogin Account Creator Automation Bot</b>\n"
        f"Create fully activated and verified [MoreLogin Antidetect Browser](https://www.morelogin.com/register) accounts in just <b>1-Click</b>.\n\n"
        f"⚡ <b>Key Features:</b>\n"
        f"• <b>1-Click Creation:</b> Automatic disposable email & instant activation link handling.\n"
        f"• <b>Custom Passwords:</b> Choose Permanent or temporary 24-Hour passwords.\n"
        f"• <b>Account History:</b> View your accounts, 1-tap copy, and export TXT files.\n"
        f"• <b>Direct Admin Support:</b> Send queries directly to the admin from chat.\n\n"
        f"👇 <i>Select an option from the menu below to get started:</i>"
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
        await update.message.reply_text("❌ Your account is temporarily suspended.")
        return

    # 1. Back to Main Menu or Cancel (Danger Red)
    if msg_text in (BTN_BACK_MAIN, BTN_CANCEL, "🔙 Main Menu", "❌ Cancel", "প্রধান মেনু", "বাতিল") or "Main Menu" in msg_text or "Cancel" in msg_text:
        context.user_data.clear()
        await log_and_notify(update, context, "Cancel / Main Menu", "click_button", "Returned to main menu")
        await update.message.reply_text(
            "🏠 <b>Main Menu:</b>\nPlease select an action below:",
            reply_markup=get_main_keyboard(is_adm),
            parse_mode="HTML"
        )
        return

    # 2. 1-Click Create Account Button (Success Green)
    if msg_text in (BTN_CREATE_ACCOUNT, "⚡ 1-Click Create Account") or "1-Click" in msg_text or "Create Account" in msg_text:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_CREATE_ACCOUNT, "click_button", "Initiated 1-click create")
        await process_create_account(update, context)
        return

    # 3. Password Menu Button (Primary Blue)
    if msg_text in (BTN_SET_PASSWORD, "🔑 Set Password") or "Set Password" in msg_text:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_SET_PASSWORD, "click_button", "Opened password settings")
        await show_password_menu(update, context)
        return

    # 4. Password Options
    if msg_text in (BTN_PWD_PERMANENT, "📌 Permanent Password") or "Permanent Password" in msg_text:
        context.user_data["awaiting_password_type"] = "permanent"
        await log_and_notify(update, context, BTN_PWD_PERMANENT, "click_button", "Selected permanent password option")
        await update.message.reply_text(
            "📌 <b>Set Permanent Password</b>\n\n"
            "Please type and send your desired password.\n"
            "<i>(Requirement: Minimum 8 characters, letters & digits mixed)</i>\n\n"
            "To cancel, tap <b>❌ Cancel</b> below.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    elif msg_text in (BTN_PWD_24H, "⏳ 24-Hour Password") or "24-Hour" in msg_text:
        context.user_data["awaiting_password_type"] = "24h"
        await log_and_notify(update, context, BTN_PWD_24H, "click_button", "Selected 24h password option")
        await update.message.reply_text(
            "⏳ <b>Set Temporary 24-Hour Password</b>\n\n"
            "Please type and send your desired password.\n"
            "<i>(Requirement: Minimum 8 characters, letters & digits mixed)</i>\n\n"
            "This password will remain active for the next <b>24 hours</b>. After 24 hours, the bot will automatically revert to Auto-Random passwords.\n\n"
            "To cancel, tap <b>❌ Cancel</b> below.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    elif msg_text in (BTN_PWD_RANDOM, "🎲 Auto Random Password") or "Random Password" in msg_text:
        context.user_data.clear()
        db.set_password_mode(user.id, "random")
        await log_and_notify(update, context, BTN_PWD_RANDOM, "click_button", "Set password to auto-random")
        await update.message.reply_text(
            "✅ <b>Auto-Random Password Mode Enabled!</b>\nA unique, high-security password will be automatically generated for every created account.",
            reply_markup=get_main_keyboard(is_adm),
            parse_mode="HTML"
        )
        return

    # 5. History Button (Primary Blue)
    if msg_text in (BTN_HISTORY, "📜 Account History") or "Account History" in msg_text or "History" in msg_text:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_HISTORY, "click_button", "Opened history")
        await show_history(update, context)
        return

    if msg_text in (BTN_HIST_COPY, "📋 Copy Format (email:pass)") or "Copy Format" in msg_text:
        await log_and_notify(update, context, BTN_HIST_COPY, "click_button", "Requested email:pass format")
        await show_history_copy_format(update, context)
        return

    elif msg_text in (BTN_HIST_EXPORT, "📥 Download TXT File") or "Download TXT" in msg_text or "TXT" in msg_text:
        await log_and_notify(update, context, BTN_HIST_EXPORT, "click_button", "Downloaded history TXT file")
        await export_history_txt(update, context)
        return

    # 6. Support Button (Primary Blue)
    if msg_text in (BTN_SUPPORT, "💬 Contact Support") or "Contact Support" in msg_text or "Support" in msg_text:
        context.user_data["awaiting_support"] = True
        await log_and_notify(update, context, BTN_SUPPORT, "click_button", "Opened support dialogue")
        await update.message.reply_text(
            "💬 <b>Contact Admin Support</b>\n\n"
            "Please send your message or query directly in this chat.\n"
            "Your message will be instantly delivered to the admin inbox.\n\n"
            "To cancel, tap <b>❌ Cancel</b> below.",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return

    # 7. Admin Panel Buttons (Danger Red)
    if (msg_text in (BTN_ADMIN_PANEL, "👑 Admin Panel") or "Admin Panel" in msg_text) and is_adm:
        context.user_data.clear()
        await log_and_notify(update, context, BTN_ADMIN_PANEL, "click_button", "Admin opened control panel")
        await show_admin_panel(update, context)
        return

    if is_adm:
        if msg_text in (BTN_ADM_LIVE, "📡 Live Click Activity") or "Live Click" in msg_text:
            await log_and_notify(update, context, BTN_ADM_LIVE, "click_button", "Viewed live feed")
            await show_live_feed(update, context)
            return
        elif msg_text in (BTN_ADM_ALERTS, "🔔 Toggle Live Push Alerts") or "Live Push" in msg_text or "Alerts" in msg_text:
            await toggle_live_alerts(update, context)
            return
        elif msg_text in (BTN_ADM_STATS, "📊 Bot Analytics") or "Analytics" in msg_text:
            await show_system_stats(update, context)
            return
        elif msg_text in (BTN_ADM_USERS, "👥 User List") or "User List" in msg_text:
            await show_user_list(update, context)
            return
        elif msg_text in (BTN_ADM_SUPPORT, "📩 Support Inbox") or "Support Inbox" in msg_text:
            await show_support_inbox(update, context)
            return
        elif msg_text in (BTN_ADM_BROADCAST, "📢 Broadcast Notice") or "Broadcast" in msg_text:
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
                f"❌ <b>Invalid Password!</b>\n\n{err_msg}\nPlease try again (or tap ❌ Cancel):",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML"
            )
            return

        db.set_user_password(user.id, msg_text, pwd_type)
        context.user_data.pop("awaiting_password_type", None)

        mode_name = "Permanent" if pwd_type == "permanent" else "24-Hour"
        await log_and_notify(
            update, context,
            button_name=f"Set Password ({pwd_type})",
            action_type="set_password",
            details=f"Set password: {msg_text}"
        )

        await update.message.reply_text(
            f"✅ <b>Password Saved Successfully!</b>\n\n"
            f"🔐 New Password: <code>{html.escape(msg_text)}</code>\n"
            f"🛡️ Mode: <b>{mode_name}</b>\n\n"
            f"Future accounts will be created using this password.",
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
                    text=f"📢 <b>Admin Announcement:</b>\n\n{html.escape(msg_text)}",
                    parse_mode="HTML"
                )
                sent_count += 1
            except Exception:
                pass

        await update.message.reply_text(
            f"✅ <b>Broadcast Completed!</b>\nDelivered to <b>{sent_count}</b> registered users.",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        return

    # C. Direct Support Message
    context.user_data.pop("awaiting_support", None)
    ticket_id = db.create_support_ticket(user.id, user.username, msg_text)

    await log_and_notify(
        update, context,
        button_name="Support Query",
        action_type="support_message",
        details=f"Ticket #{ticket_id}: {msg_text}"
    )

    uname_str = f"@{user.username}" if user.username else f"ID: {user.id}"
    admin_alert = (
        f"📩 <b>[New Support Message – Ticket #{ticket_id}]</b>\n"
        f"👤 From: <b>{html.escape(user.full_name)}</b> ({uname_str})\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"⏰ Time: <code>{datetime.now().strftime('%Y-%m-%d %I:%M %p')}</code>\n\n"
        f"💬 <b>Message:</b>\n"
        f"<i>{html.escape(msg_text)}</i>\n\n"
        f"👉 To reply, send: <code>/reply {ticket_id} Your message</code>"
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
        "✅ <b>Your message has been sent to the admin!</b>\n"
        "The admin will review your inquiry and respond shortly. Thank you!",
        reply_markup=get_main_keyboard(is_adm),
        parse_mode="HTML"
    )

# ── Account Creation Logic ────────────────────────────────────
async def process_create_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_adm = is_admin(user.id)

    status_msg = await update.message.reply_text(
        "⚡ <b>1-Click Account Creation in progress...</b>\nPlease wait a moment...",
        parse_mode="HTML"
    )

    async def progress_update(step_text: str):
        try:
            await status_msg.edit_text(
                text=f"⚡ <b>MoreLogin Account Creation:</b>\n\n{step_text}",
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
            button_name="✅ Account Ready",
            action_type="account_success",
            details=f"Email: {email} | Pass: {password}"
        )

        success_text = (
            f"🎉 <b>Congratulations! Your MoreLogin Account is Ready!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📧 <b>Email:</b> <code>{email}</code>\n"
            f"🔑 <b>Password:</b> <code>{password}</code>\n"
            f"🛡️ <b>Password Type:</b> {pwd_type_desc}\n"
            f"✅ <b>Status:</b> Fully Activated & Verified\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📬 <b>Mailbox Link:</b> <a href=\"{mailbox_url}\">Open Inbox (muellfach.de)</a>\n\n"
            f"💡 <i>(Tap on email or password to copy instantly)</i>"
        )

        await status_msg.edit_text(
            text=success_text,
            reply_markup=None,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        await update.message.reply_text(
            "👇 <i>To create another account, tap '⚡ 1-Click Create Account' below:</i>",
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
            f"❌ <b>Account Creation Failed!</b>\n\n"
            f"⚠️ Reason: <code>{html.escape(err)}</code>\n\n"
            f"Please try again shortly or contact support."
        )
        await status_msg.edit_text(
            text=fail_text,
            parse_mode="HTML"
        )
        await update.message.reply_text(
            "Use the menu below to try again:",
            reply_markup=get_main_keyboard(is_adm)
        )

# ── Password Menu Logic ────────────────────────────────────
async def show_password_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    settings = db.get_user_settings(user.id)
    p_type = settings.get("password_type", "random")
    current_pwd = settings.get("custom_password") or "Not Set"
    expires_at_str = settings.get("password_expires_at")

    if p_type == "permanent":
        type_str = "📌 Permanent"
    elif p_type == "24h":
        rem = ""
        if expires_at_str:
            try:
                exp = datetime.fromisoformat(expires_at_str)
                delta = exp - datetime.now()
                if delta.total_seconds() > 0:
                    hours, rem_sec = divmod(int(delta.total_seconds()), 3600)
                    mins = rem_sec // 60
                    rem = f" ({hours}h {mins}m remaining)"
                else:
                    rem = " (Expired)"
            except Exception:
                pass
        type_str = f"⏳ 24-Hour{rem}"
    else:
        type_str = "🎲 Auto-Random (Unique strong password per account)"

    text = (
        f"🔑 <b>Password Settings & Management</b>\n\n"
        f"🛡️ Current Mode: <b>{type_str}</b>\n"
        f"🔐 Configured Password: <code>{html.escape(current_pwd)}</code>\n\n"
        f"<i>Select an option below to configure:</i>\n\n"
        f"• <b>Permanent Password:</b> Uses this exact password for all future accounts.\n"
        f"• <b>24-Hour Password:</b> Valid for 24 hours, then reverts to Auto-Random.\n"
        f"• <b>Auto-Random:</b> Generates a strong unique password on every creation."
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
            f"📜 <b>Account Creation History</b>\n\n"
            f"⚠️ You have not created any MoreLogin accounts yet.\n"
            f"Tap <b>⚡ 1-Click Create Account</b> below to create your first account."
        )
        await update.message.reply_text(
            text=text,
            reply_markup=get_history_keyboard(has_accounts=False),
            parse_mode="HTML"
        )
        return

    text = f"📜 <b>Your Created Accounts ({total_count} Total):</b>\n\n"
    for i, acc in enumerate(accounts, 1):
        dt = acc['created_at'].split()[0] if ' ' in acc['created_at'] else acc['created_at']
        text += (
            f"<b>{i}.</b> 📧 <code>{acc['email']}</code>\n"
            f"   🔑 <code>{acc['password']}</code>\n"
            f"   📅 <i>{dt}</i> | ✅ Activated\n\n"
        )

    text += "💡 <i>Tap below to copy in email:pass format or export a TXT file:</i>"

    await update.message.reply_text(
        text=text,
        reply_markup=get_history_keyboard(has_accounts=True),
        parse_mode="HTML"
    )

async def show_history_copy_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    accounts = db.get_user_accounts(user.id, limit=50)
    if not accounts:
        await update.message.reply_text("No history found.", reply_markup=get_history_keyboard(False))
        return

    copy_lines = [f"{acc['email']}:{acc['password']}" for acc in accounts]
    joined = "\n".join(copy_lines)

    text = (
        f"📋 <b>Copy Format (email:pass):</b>\n\n"
        f"<code>{joined}</code>\n\n"
        f"👆 <i>Tap on the code block above to copy all lines in 1 tap.</i>"
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
        await update.message.reply_text("No history found to export.")
        return

    lines = [f"{acc['email']}:{acc['password']}" for acc in accounts]
    content = "\n".join(lines)

    bio = io.BytesIO(content.encode('utf-8'))
    bio.name = f"morelogin_accounts_{user.id}.txt"

    await context.bot.send_document(
        chat_id=user.id,
        document=bio,
        caption=f"📥 <b>Your {len(accounts)} MoreLogin Accounts (email:password)</b>",
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
            "Usage: <code>/reply &lt;ticket_id&gt; &lt;your message&gt;</code>",
            parse_mode="HTML"
        )
        return

    try:
        ticket_id = int(context.args[0])
        reply_msg = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ Ticket ID must be a number.")
        return

    target_uid = db.reply_support_ticket(ticket_id, reply_msg)
    if not target_uid:
        await update.message.reply_text("❌ Ticket not found.")
        return

    try:
        await context.bot.send_message(
            chat_id=target_uid,
            text=(
                f"👨‍💻 <b>Admin Support Response:</b>\n\n"
                f"💬 <i>{html.escape(reply_msg)}</i>\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"If you have further questions, feel free to message back."
            ),
            parse_mode="HTML"
        )
        await update.message.reply_text(f"✅ Reply sent to user for ticket #{ticket_id}!")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to deliver message to user: {e}")
