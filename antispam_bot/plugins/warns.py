import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from storage import add_warn, get_warns, reset_warns
from .helpers import is_admin

logger = logging.getLogger(__name__)

MAX_WARNS = 3  # auto-ban after this many warns


@Client.on_message(filters.command("warn") & filters.group)
async def warn_user(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply_text("Reply to a user's message with /warn to warn them.")

    target = message.reply_to_message.from_user
    if await is_admin(client, message.chat.id, target.id):
        return await message.reply_text("Can't warn another admin.")

    count = add_warn(message.chat.id, target.id)

    if count >= MAX_WARNS:
        try:
            await client.ban_chat_member(message.chat.id, target.id)
            reset_warns(message.chat.id, target.id)
            await message.reply_text(
                f"🚫 {target.mention} reached {MAX_WARNS} warns and has been banned."
            )
        except Exception as e:
            logger.warning(f"auto-ban failed: {e}")
            await message.reply_text(
                f"⚠️ {target.mention} reached {MAX_WARNS} warns, but I couldn't ban them "
                f"(check my admin permissions)."
            )
    else:
        await message.reply_text(
            f"⚠️ {target.mention} has been warned ({count}/{MAX_WARNS}). "
            f"Reaching {MAX_WARNS} warns results in a ban."
        )


@Client.on_message(filters.command("warns") & filters.group)
async def show_warns(client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif message.from_user:
        target = message.from_user
    else:
        return await message.reply_text("Couldn't identify a user.")

    count = get_warns(message.chat.id, target.id)
    await message.reply_text(f"{target.mention} has {count}/{MAX_WARNS} warns.")


@Client.on_message(filters.command("resetwarns") & filters.group)
async def reset_user_warns(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")

    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply_text("Reply to a user's message with /resetwarns to clear their warns.")

    target = message.reply_to_message.from_user
    reset_warns(message.chat.id, target.id)
    await message.reply_text(f"✅ Warns cleared for {target.mention}.")
