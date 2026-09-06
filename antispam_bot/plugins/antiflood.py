import logging
import time
from collections import defaultdict, deque

from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.types import ChatPermissions, Message

import config
from storage import get_group_settings, set_group_setting
from .helpers import is_admin

logger = logging.getLogger(__name__)

# In-memory recent-message timestamps per (chat_id, user_id).
# Resets if the bot restarts - that's fine, flood control only needs recent history.
_message_log = defaultdict(deque)

MUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)


@Client.on_message(filters.command("antiflood") & filters.group)
async def toggle_antiflood(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split()
    if len(args) != 2 or args[1].lower() not in ("on", "off"):
        return await message.reply_text(
            "Usage:\n<code>/antiflood on</code>\n<code>/antiflood off</code>"
        )

    enable = args[1].lower() == "on"
    set_group_setting(message.chat.id, "antiflood", enable)
    await message.reply_text(f"Anti-Flood is now {'✅ ON' if enable else '❌ OFF'}")


@Client.on_message(filters.command("setflood") & filters.group)
async def set_flood_limit(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split()
    if len(args) != 3 or not args[1].isdigit() or not args[2].isdigit():
        return await message.reply_text(
            "Usage: <code>/setflood &lt;messages&gt; &lt;seconds&gt;</code>\n"
            "Example: <code>/setflood 5 10</code>"
        )

    count, seconds = int(args[1]), int(args[2])
    set_group_setting(message.chat.id, "flood_count", count)
    set_group_setting(message.chat.id, "flood_seconds", seconds)
    await message.reply_text(f"✅ Flood limit set to {count} messages per {seconds} seconds.")


@Client.on_message(filters.group & filters.incoming, group=6)
async def check_flood(client, message: Message):
    try:
        if not message.from_user:
            return

        settings = get_group_settings(message.chat.id)
        if not settings.get("antiflood"):
            return

        if await is_admin(client, message.chat.id, message.from_user.id):
            return

        limit = settings.get("flood_count", config.FLOOD_LIMIT)
        window = settings.get("flood_seconds", config.FLOOD_SECONDS)

        key = (message.chat.id, message.from_user.id)
        now = time.time()
        log = _message_log[key]
        log.append(now)
        while log and now - log[0] > window:
            log.popleft()

        if len(log) > limit:
            log.clear()
            try:
                await client.restrict_chat_member(
                    message.chat.id, message.from_user.id, permissions=MUTED_PERMISSIONS
                )
                await message.reply_text(
                    f"🔇 {message.from_user.mention} has been muted for spamming messages too fast."
                )
            except ChatAdminRequired:
                await message.reply_text(
                    "⚠️ I need admin rights with 'Restrict Members' permission to mute spammers."
                )
    except Exception as e:
        logger.warning(f"antiflood error: {e}")
