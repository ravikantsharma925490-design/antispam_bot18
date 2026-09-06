from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
 
import config
from storage import get_group_settings
from .helpers import get_missing_join_buttons, is_admin
 
START_TEXT = (
    "👋 <b>Hey! I'm an Anti-Spam bot.</b>\n\n"
    "I protect your Telegram groups from spam links, flooding, bad words, "
    "and fake/bot accounts.\n\n"
    "<b>How to set me up:</b>\n"
    "1️⃣ Add me to your group\n"
    "2️⃣ Make me an <b>Admin</b> (with Delete Messages + Restrict Members + Ban Users)\n"
    "3️⃣ In the group, send <code>/set</code> (as an admin) — this turns ON all "
    "protections at once (anti-link, anti-flood, bad-words, captcha, welcome)\n\n"
    "Send <code>/help</code> anytime to see every command, or <code>/settings</code> "
    "to check what's currently enabled."
)
 
 
def _join_prompt_markup(missing_buttons):
    rows = [[btn] for btn in missing_buttons]
    rows.append([InlineKeyboardButton("♻️ Try Again", callback_data="check_join")])
    return InlineKeyboardMarkup(rows)
 
 
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    missing = await get_missing_join_buttons(client, message.from_user.id)
    if missing:
        return await message.reply_text(
            "🛑 Please join the channel(s)/group(s) below before using this bot, "
            "then tap <b>Try Again</b>.",
            reply_markup=_join_prompt_markup(missing),
            parse_mode=enums.ParseMode.HTML,
        )
 
    await message.reply_text(START_TEXT, parse_mode=enums.ParseMode.HTML)
 
 
@Client.on_callback_query(filters.regex("^check_join$"))
async def check_join_callback(client, callback_query: CallbackQuery):
    missing = await get_missing_join_buttons(client, callback_query.from_user.id)
    if missing:
        try:
            await callback_query.message.edit_reply_markup(_join_prompt_markup(missing))
        except Exception:
            pass
        return await callback_query.answer(
            "You still haven't joined everything required.", show_alert=True
        )
 
    await callback_query.answer("✅ Verified!")
    await callback_query.message.edit_text(START_TEXT, parse_mode=enums.ParseMode.HTML)
 
 
@Client.on_message(filters.command("start") & filters.group)
async def group_start_cmd(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
 
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use /start in a group.")
 
    await message.reply_text(
        f"✅ I'm active in <b>{message.chat.title}</b>!\n\n"
        "Use <code>/set</code> to turn ON all protections at once, or /help to "
        "see individual commands and /settings to view what's currently enabled.",
        parse_mode=enums.ParseMode.HTML,
    )
 
 
@Client.on_message(filters.command("help"))
async def help_cmd(client, message: Message):
    await message.reply_text(
        "<b>📖 Commands</b>\n\n"
        "<code>/set</code> — turn ON all protections at once (recommended quick setup)\n\n"
        "<u>Anti-Spam</u>\n"
        "<code>/antilink on|off</code> — delete links/@usernames from non-admins\n"
        "<code>/antiflood on|off</code> — auto-mute users spamming messages\n"
        "<code>/setflood &lt;count&gt; &lt;seconds&gt;</code> — customize flood threshold\n"
        "<code>/badwords on|off</code> — enable bad-word filtering\n"
        "<code>/addword &lt;word&gt;</code>, <code>/removeword &lt;word&gt;</code>, <code>/wordlist</code>\n\n"
        "<u>Moderation</u> (reply to a user's message)\n"
        "<code>/warn</code>, <code>/warns</code>, <code>/resetwarns</code> — 3 warns = auto-ban\n"
        "<code>/ban</code>, <code>/unban</code>, <code>/kick</code>, <code>/mute</code>, <code>/unmute</code>\n\n"
        "<u>Welcome</u>\n"
        "<code>/welcome on|off</code>, <code>/welcome set &lt;message&gt;</code>\n"
        "<code>/welcome setimage</code> (reply to a photo), <code>/welcome resetimage</code>\n"
        "<code>/goodbye on|off</code>\n\n"
        "<u>New Member Verification</u>\n"
        "<code>/captcha on|off</code> — mute new members until they tap a button to verify they're human\n\n"
        "<u>Reporting</u> (reply to a message)\n"
        "<code>/report [reason]</code> — flag a message to admins; they get quick Mute/Ban buttons\n\n"
        "<code>/settings</code> — show current settings for this group\n\n"
        "All commands (except /start, /help) must be used by a group admin.",
        parse_mode=enums.ParseMode.HTML,
    )
 
 
@Client.on_message(filters.command("settings") & filters.group)
async def show_settings(client, message: Message):
    s = get_group_settings(message.chat.id)
    antilink = "✅ ON" if s.get("antilink") else "❌ OFF"
    antiflood = "✅ ON" if s.get("antiflood") else "❌ OFF"
    badwords = "✅ ON" if s.get("badwords") else "❌ OFF"
    welcome = "✅ ON" if s.get("welcome", True) else "❌ OFF"
    goodbye = "✅ ON" if s.get("goodbye", False) else "❌ OFF"
    captcha = "✅ ON" if s.get("captcha") else "❌ OFF"
    flood_count = s.get("flood_count", config.FLOOD_LIMIT)
    flood_seconds = s.get("flood_seconds", config.FLOOD_SECONDS)
    await message.reply_text(
        f"<b>⚙️ Settings for {message.chat.title}</b>\n\n"
        f"Anti-Link: {antilink}\n"
        f"Anti-Flood: {antiflood} ({flood_count} msgs / {flood_seconds}s)\n"
        f"Bad-word filter: {badwords}\n"
        f"Welcome messages: {welcome}\n"
        f"Goodbye messages: {goodbye}\n"
        f"Captcha verification: {captcha}",
        parse_mode=enums.ParseMode.HTML,
    )
 
