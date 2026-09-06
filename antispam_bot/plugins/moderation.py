import logging

from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid
from pyrogram.types import ChatPermissions, Message

from .helpers import is_admin

logger = logging.getLogger(__name__)

FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)

MUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)


def _get_target(message: Message):
    """Returns the target user from a reply, or None."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None


async def _require_admin_and_target(client, message: Message):
    """Shared checks for all mod commands. Returns target user or None (already replied)."""
    if not message.from_user:
        await message.reply_text("Anonymous admins can't use this command.")
        return None
    if not await is_admin(client, message.chat.id, message.from_user.id):
        await message.reply_text("⚠️ Only group admins can use this command.")
        return None
    target = _get_target(message)
    if not target:
        await message.reply_text("Reply to the user's message with this command.")
        return None
    if await is_admin(client, message.chat.id, target.id):
        await message.reply_text("Can't act on another admin.")
        return None
    return target


@Client.on_message(filters.command("ban") & filters.group)
async def ban_cmd(client, message: Message):
    target = await _require_admin_and_target(client, message)
    if not target:
        return
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await message.reply_text(f"🚫 {target.mention} has been banned.")
    except (ChatAdminRequired, UserAdminInvalid):
        await message.reply_text("⚠️ I need admin rights with 'Ban Users' permission.")
    except Exception as e:
        logger.warning(f"ban error: {e}")
        await message.reply_text(f"⚠️ Couldn't ban: {e}")


@Client.on_message(filters.command("unban") & filters.group)
async def unban_cmd(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split()
    target = _get_target(message)
    if target:
        target_id = target.id
    elif len(args) == 2 and args[1].lstrip("-").isdigit():
        target_id = int(args[1])
    else:
        return await message.reply_text("Reply to the user, or use /unban <user_id>.")

    try:
        await client.unban_chat_member(message.chat.id, target_id)
        await message.reply_text("✅ User has been unbanned.")
    except Exception as e:
        logger.warning(f"unban error: {e}")
        await message.reply_text(f"⚠️ Couldn't unban: {e}")


@Client.on_message(filters.command("kick") & filters.group)
async def kick_cmd(client, message: Message):
    target = await _require_admin_and_target(client, message)
    if not target:
        return
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await client.unban_chat_member(message.chat.id, target.id)  # ban+unban = kick
        await message.reply_text(f"👢 {target.mention} has been kicked.")
    except (ChatAdminRequired, UserAdminInvalid):
        await message.reply_text("⚠️ I need admin rights with 'Ban Users' permission.")
    except Exception as e:
        logger.warning(f"kick error: {e}")
        await message.reply_text(f"⚠️ Couldn't kick: {e}")


@Client.on_message(filters.command("mute") & filters.group)
async def mute_cmd(client, message: Message):
    target = await _require_admin_and_target(client, message)
    if not target:
        return
    try:
        await client.restrict_chat_member(message.chat.id, target.id, permissions=MUTED_PERMISSIONS)
        await message.reply_text(f"🔇 {target.mention} has been muted.")
    except (ChatAdminRequired, UserAdminInvalid):
        await message.reply_text("⚠️ I need admin rights with 'Restrict Members' permission.")
    except Exception as e:
        logger.warning(f"mute error: {e}")
        await message.reply_text(f"⚠️ Couldn't mute: {e}")


@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(client, message: Message):
    target = await _require_admin_and_target(client, message)
    if not target:
        return
    try:
        await client.restrict_chat_member(message.chat.id, target.id, permissions=FULL_PERMISSIONS)
        await message.reply_text(f"🔊 {target.mention} has been unmuted.")
    except (ChatAdminRequired, UserAdminInvalid):
        await message.reply_text("⚠️ I need admin rights with 'Restrict Members' permission.")
    except Exception as e:
        logger.warning(f"unmute error: {e}")
        await message.reply_text(f"⚠️ Couldn't unmute: {e}")
