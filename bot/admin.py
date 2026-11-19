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
        f"🔴 <b>[রিয়েলটাইম বাটন ক্লিক নোটিফিকেশন]</b>\n"
        f"⏰ সময়: <code>{now_str}</code>\n"
        f"👤 ইউজার: <b>{user_display}</b>\n"
        f"🆔 আইডি: <code>{user_id}</code>\n"
        f"🔘 বাটন/অ্যাকশন: <b>{html.escape(button_name)}</b>\n"
    )
    if details:
        alert_text += f"📝 তথ্য: <i>{html.escape(details)}</i>\n"

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
            "❌ শুধুমাত্র অনুমোদিত অ্যাডমিন এই প্যানেল দেখতে পারেন।",
            reply_markup=get_main_keyboard(False)
        )
        return

    alerts_on = db.is_live_alerts_enabled(user_id)
    alert_status = "চালু (ON) 🔔" if alerts_on else "বন্ধ (OFF) 🔕"
    stats = db.get_system_stats()

    text = (
        f"👑 <b>অ্যাডমিন কন্ট্রোল প্যানেল (Admin Panel)</b>\n\n"
        f"📊 <b>তাৎক্ষণিক পরিসংখ্যান:</b>\n"
        f"• মোট ইউজার: <b>{stats['total_users']}</b> জন\n"
        f"• মোট তৈরি একাউন্ট: <b>{stats['total_accounts']}</b> টি\n"
        f"• আজকে তৈরি একাউন্ট: <b>{stats['today_accounts']}</b> টি\n"
        f"• আজকের মোট বাটন ক্লিক: <b>{stats['today_clicks']}</b> বার\n"
        f"• উত্তর বাকি সাপোর্ট মেসেজ: <b>{stats['pending_support']}</b> টি\n"
        f"• লাইভ ক্লিক অ্যালার্ট: <b>{alert_status}</b>\n\n"
        f"🌐 <b>লাইভ ব্রাউজার অটোমেশন ড্যাশবোর্ড:</b>\n"
        f"পিসির ব্রাউজারে খুলুন: <code>http://localhost:8080/</code>\n\n"
        f"<i>নিচের মেনু বাটনগুলো দিয়ে মনিটরিং ও কন্ট্রোল করুন:</i>"
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
        msg = "🔔 <b>লাইভ ক্লিক পুশ অ্যালার্ট চালু করা হয়েছে!</b>\nএখন থেকে যেকোনো ইউজার যেকোনো বাটনে চাপ দিলেই আপনি সাথে সাথে টেলিগ্রাম মেসেজে অ্যালার্ট পাবেন।"
    else:
        msg = "🔕 <b>লাইভ ক্লিক পুশ অ্যালার্ট বন্ধ করা হয়েছে!</b>\nআপনি চাইলে যেকোনো সময় পুনরায় চালু করতে পারবেন।"

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
        text = "📡 <b>সাম্প্রতিক কোনো অ্যাক্টিভিটি পাওয়া যায়নি।</b>"
    else:
        text = "📡 <b>রিয়েলটাইম ইউজার অ্যাক্টিভিটি ফিড (সর্বশেষ ১৫টি):</b>\n\n"
        for act in activities:
            time_val = act['timestamp'].split()[-1] if ' ' in act['timestamp'] else act['timestamp']
            u_name = f"@{act['username']}" if act['username'] else f"ID: {act['user_id']}"
            btn = act['button_name']
            det = f" - <i>{html.escape(act['details'])}</i>" if act['details'] else ""
            text += f"• <code>[{time_val}]</code> <b>{html.escape(u_name)}</b> 👉 <b>{html.escape(btn)}</b>{det}\n"

    text += "\n<i>(ইউজাররা বাটনে চাপ দিলে ডাটাবেসে রিয়েলটাইমে রেকর্ড হয়)</i>"
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
        f"📊 <b>বিস্তারিত বট অ্যানালিটিক্স ও রিপোর্ট</b>\n\n"
        f"👥 মোট রেজিস্টার্ড ইউজার: <b>{stats['total_users']}</b> জন\n"
        f"⚡ মোট তৈরি করা MoreLogin একাউন্ট: <b>{stats['total_accounts']}</b> টি\n"
        f"📅 আজকে তৈরি একাউন্ট: <b>{stats['today_accounts']}</b> টি\n"
        f"🖱️ আজকে বট ক্লিক/ইন্টারেকশন: <b>{stats['today_clicks']}</b> বার\n"
        f"📩 পেন্ডিং সাপোর্ট রিকোয়েস্ট: <b>{stats['pending_support']}</b> টি\n"
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
    text = f"👥 <b>বট ইউজারদের তালিকা (মোট {len(user_ids)} জন):</b>\n\n"
    for uid in user_ids[:20]:
        cnt = db.get_user_account_count(uid)
        text += f"• ইউজার আইডি: <code>{uid}</code> (তৈরিকৃত একাউন্ট: <b>{cnt}</b> টি)\n"
    if len(user_ids) > 20:
        text += f"\n<i>...এবং আরও {len(user_ids)-20} জন ইউজার।</i>"
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
            text="📩 <b>বর্তমানে কোনো পেন্ডিং সাপোর্ট মেসেজ নেই!</b>\nসব মেসেজের সমাধান হয়েছে।",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        return

    text = f"📩 <b>পেন্ডিং সাপোর্ট মেসেজ (মোট {len(pending)} টি):</b>\n\n"
    for t in pending[:5]:
        uname = f"@{t['username']}" if t['username'] else f"ID: {t['user_id']}"
        text += (
            f"🎫 <b>টিকেট #{t['id']}</b> | ইউজার: <b>{html.escape(uname)}</b>\n"
            f"💬 মেসেজ: <i>{html.escape(t['message'])}</i>\n"
            f"⏰ সময়: <code>{t['created_at']}</code>\n"
            f"👉 রিপ্লাই দিতে টাইপ করুন: <code>/reply {t['id']} আপনার উত্তর</code>\n\n"
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
            "📢 <b>সকল ইউজারের কাছে ব্রডকাস্ট নোটিশ পাঠান</b>\n\n"
            "আপনি সকল ইউজারকে যে নোটিশ পাঠাতে চান তা লিখে মেসেজ আকারে পাঠান।\n"
            "বাতিল করতে চাইলে নিচের <b>❌ বাতিল</b> বাটনে চাপ দিন।"
        ),
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
