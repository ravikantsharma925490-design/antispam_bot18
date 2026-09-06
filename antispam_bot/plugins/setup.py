import logging

from pyrogram import Client, enums, filters
from pyrogram.types import Message

from storage import set_group_setting
from .helpers import is_admin

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("set") & filters.group)
async def setup_all(client: Client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    chat_id = message.chat.id

    set_group_setting(chat_id, "antilink", True)
    set_group_setting(chat_id, "antiflood", True)
    set_group_setting(chat_id, "badwords", True)
    set_group_setting(chat_id, "captcha", True)
    set_group_setting(chat_id, "welcome", True)

    await message.reply_text(
        "✅ <b>All protections have been turned ON for this group:</b>\n\n"
        "🔗 Anti-Link — ON\n"
        "🌊 Anti-Flood — ON\n"
        "🤬 Bad-word filter — ON\n"
        "🤖 Captcha for new members — ON\n"
        "👋 Welcome messages — ON\n\n"
        "Use <code>/settings</code> anytime to check the current status, "
        "or turn any of these off individually (e.g. <code>/antilink off</code>).",
        parse_mode=enums.ParseMode.HTML,
    )
