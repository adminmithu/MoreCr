import html
from datetime import datetime
from telegram import Update, Bot
from telegram.ext import ContextTypes

from config import ADMIN_IDS, is_admin
from database.db import Database
from bot.keyboards import (
    get_admin_keyboard,
    get_cancel_keyboard,
    get_main_keyboard
)

db = Database()

async def notify_admins_activity(
    bot: Bot,
    user_id: int,
    username: str,
    full_name: str,
    button_name: str,
    action_type: str,
    details: str = ""
):
    """
    Sends real-time push alert to admins when any user clicks a button or takes an action.
    """
    now_str = datetime.now().strftime("%I:%M:%S %p")
    user_display = f"{html.escape(full_name or 'User')} (@{html.escape(username)})" if username else html.escape(full_name or 'User')
    
    alert_text = (
        f"🔴 <b>[Real-time Button Click Alert]</b>\n"
        f"⏰ Time: <code>{now_str}</code>\n"
        f"👤 User: <b>{user_display}</b>\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"🔘 Action/Button: <b>{html.escape(button_name)}</b>\n"
    )
    if details:
        alert_text += f"📝 Details: <i>{html.escape(details)}</i>\n"

    for admin_id in ADMIN_IDS:
        if admin_id == user_id:
            continue
        try:
            if db.is_live_alerts_enabled(admin_id):
                await bot.send_message(
                    chat_id=admin_id,
                    text=alert_text,
                    parse_mode="HTML"
                )
        except Exception:
            pass

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text(
            "❌ Access denied: Authorized admins only.",
            reply_markup=get_main_keyboard(False)
        )
        return

    alerts_on = db.is_live_alerts_enabled(user_id)
    alert_status = "Active 🔔" if alerts_on else "Disabled 🔕"
    stats = db.get_system_stats()

    text = (
        f"👑 <b>Admin Control Panel</b>\n\n"
        f"📊 <b>Instant Analytics:</b>\n"
        f"• Total Users: <b>{stats['total_users']}</b>\n"
        f"• Total Accounts Created: <b>{stats['total_accounts']}</b>\n"
        f"• Accounts Created Today: <b>{stats['today_accounts']}</b>\n"
        f"• Button Clicks Today: <b>{stats['today_clicks']}</b>\n"
        f"• Pending Support Messages: <b>{stats['pending_support']}</b>\n"
        f"• Real-time Push Alerts: <b>{alert_status}</b>\n\n"
        f"🌐 <b>Live Browser Automation Dashboard:</b>\n"
        f"Open on PC browser: <code>http://localhost:8080/</code>\n\n"
        f"<i>Select an option below to manage the bot:</i>"
    )

    await update.message.reply_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

async def toggle_live_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    new_status = db.toggle_admin_live_alerts(user_id)
    if new_status:
        msg = "🔔 <b>Live Click Push Alerts Enabled!</b>\nYou will now receive instant Telegram messages whenever any user clicks any button."
    else:
        msg = "🔕 <b>Live Click Push Alerts Disabled!</b>\nYou can re-enable alerts anytime from this menu."

    await update.message.reply_text(
        text=msg,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

async def show_live_feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    activities = db.get_recent_activities(limit=15)
    if not activities:
        text = "📡 <b>No recent user activities found.</b>"
    else:
        text = "📡 <b>Real-time User Activity Feed (Last 15 Events):</b>\n\n"
        for act in activities:
            time_val = act['timestamp'].split()[-1] if ' ' in act['timestamp'] else act['timestamp']
            u_name = f"@{act['username']}" if act['username'] else f"ID: {act['user_id']}"
            btn = act['button_name']
            det = f" - <i>{html.escape(act['details'])}</i>" if act['details'] else ""
            text += f"• <code>[{time_val}]</code> <b>{html.escape(u_name)}</b> 👉 <b>{html.escape(btn)}</b>{det}\n"

    text += "\n<i>(Recorded live in database on every user interaction)</i>"
    await update.message.reply_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

async def show_system_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    stats = db.get_system_stats()
    text = (
        f"📊 <b>Detailed Bot Analytics & Performance</b>\n\n"
        f"👥 Total Registered Users: <b>{stats['total_users']}</b>\n"
        f"⚡ Total MoreLogin Accounts: <b>{stats['total_accounts']}</b>\n"
        f"📅 Accounts Created Today: <b>{stats['today_accounts']}</b>\n"
        f"🖱️ Bot Interactions Today: <b>{stats['today_clicks']}</b>\n"
        f"📩 Pending Support Queries: <b>{stats['pending_support']}</b>\n"
    )
    await update.message.reply_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

async def show_user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    user_ids = db.get_all_user_ids()
    text = f"👥 <b>Registered Users List ({len(user_ids)} Total):</b>\n\n"
    for uid in user_ids[:20]:
        cnt = db.get_user_account_count(uid)
        text += f"• User ID: <code>{uid}</code> (Created Accounts: <b>{cnt}</b>)\n"
    if len(user_ids) > 20:
        text += f"\n<i>...and {len(user_ids)-20} more users.</i>"
    await update.message.reply_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

async def show_support_inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    pending = db.get_pending_support_tickets()
    if not pending:
        await update.message.reply_text(
            text="📩 <b>Support Inbox is Clear!</b>\nThere are no pending support tickets.",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        return

    text = f"📩 <b>Pending Support Messages ({len(pending)} Total):</b>\n\n"
    for t in pending[:5]:
        uname = f"@{t['username']}" if t['username'] else f"ID: {t['user_id']}"
        text += (
            f"🎫 <b>Ticket #{t['id']}</b> | User: <b>{html.escape(uname)}</b>\n"
            f"💬 Message: <i>{html.escape(t['message'])}</i>\n"
            f"⏰ Time: <code>{t['created_at']}</code>\n"
            f"👉 To reply, send: <code>/reply {t['id']} Your response</code>\n\n"
        )
    await update.message.reply_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

async def start_broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    context.user_data["awaiting_broadcast"] = True
    await update.message.reply_text(
        text=(
            "📢 <b>Broadcast Announcement to All Users</b>\n\n"
            "Please type your message and send it now.\n"
            "It will be delivered to all registered bot users.\n\n"
            "To cancel, tap <b>❌ Cancel</b> below."
        ),
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
