import logging

from pyrogram import Client, enums, filters
from pyrogram.types import Message

import config

logger = logging.getLogger(__name__)


@Client.on_message(filters.new_chat_members & filters.group, group=1)
async def log_new_group(client: Client, message: Message):
    try:
        if not config.LOG_CHANNEL:
            return  # feature disabled - no LOG_CHANNEL configured

        me = await client.get_me()
        added_by_bot = any(member.id == me.id for member in message.new_chat_members)
        if not added_by_bot:
            return  # a regular member joined, not the bot itself - nothing to log here

        chat = message.chat
        try:
            member_count = await client.get_chat_members_count(chat.id)
        except Exception:
            member_count = "N/A"

        added_by = message.from_user.mention if message.from_user else "Unknown"

        text = (
            f"➕ <b>Added to a new group!</b>\n\n"
            f"<b>Name:</b> {chat.title}\n"
            f"<b>ID:</b> <code>{chat.id}</code>\n"
            f"<b>Members:</b> {member_count}\n"
            f"<b>Added by:</b> {added_by}"
        )
        await client.send_message(config.LOG_CHANNEL, text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.warning(f"group log (added) error: {e}")


@Client.on_message(filters.left_chat_member & filters.group, group=1)
async def log_removed_from_group(client: Client, message: Message):
    try:
        if not config.LOG_CHANNEL:
            return

        me = await client.get_me()
        left_member = message.left_chat_member
        if not left_member or left_member.id != me.id:
            return  # a regular member left, not the bot itself

        chat = message.chat
        text = (
            f"➖ <b>Removed from a group.</b>\n\n"
            f"<b>Name:</b> {chat.title}\n"
            f"<b>ID:</b> <code>{chat.id}</code>"
        )
        await client.send_message(config.LOG_CHANNEL, text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        logger.warning(f"group log (removed) error: {e}")
