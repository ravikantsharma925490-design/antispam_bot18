import asyncio
import logging
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from storage import get_group_settings, set_group_setting
from .helpers import is_admin

logger = logging.getLogger(__name__)

# Matches http(s) links, t.me links, telegram.me links, bare www. links,
# and @username mentions (which Telegram also turns into clickable links).
LINK_PATTERN = re.compile(
    r"(https?://\S+)|(t\.me/\S+)|(telegram\.me/\S+)|(www\.\S+\.\S+)|(@[a-zA-Z]\w{3,31})",
    re.IGNORECASE,
)


@Client.on_message(filters.command("antilink") & filters.group)
async def toggle_antilink(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split()
    if len(args) != 2 or args[1].lower() not in ("on", "off"):
        return await message.reply_text(
            "Usage:\n<code>/antilink on</code>\n<code>/antilink off</code>"
        )

    enable = args[1].lower() == "on"
    set_group_setting(message.chat.id, "antilink", enable)
    await message.reply_text(f"Anti-Link is now {'✅ ON' if enable else '❌ OFF'}")


@Client.on_message(filters.group & filters.text & filters.incoming, group=5)
async def delete_links(client, message: Message):
    try:
        if not message.from_user:
            return  # anonymous admin / channel-linked message, skip

        settings = get_group_settings(message.chat.id)
        if not settings.get("antilink"):
            return  # feature disabled for this group

        if not LINK_PATTERN.search(message.text or ""):
            return  # no link found

        if await is_admin(client, message.chat.id, message.from_user.id):
            return  # never touch an admin's message

        chat_id = message.chat.id
        mention = message.from_user.mention

        await message.delete()
        warn = await client.send_message(
            chat_id,
            f"⚠️ {mention}, links/usernames aren't allowed here! Your message was removed.",
        )
        await asyncio.sleep(8)
        try:
            await warn.delete()
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"antilink error: {e}")
