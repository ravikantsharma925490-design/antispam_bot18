import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from storage import get_group_settings, set_group_setting
from .helpers import is_admin

logger = logging.getLogger(__name__)

CAPTCHA_TIMEOUT = 60  # seconds the new member has to verify

# (chat_id, user_id) -> id of the captcha prompt message currently pending
_pending = {}

MUTE_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)
FULL_PERMS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


@Client.on_message(filters.command("captcha") & filters.group)
async def toggle_captcha(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split()
    if len(args) != 2 or args[1].lower() not in ("on", "off"):
        return await message.reply_text(
            "Usage:\n<code>/captcha on</code>\n<code>/captcha off</code>"
        )

    enable = args[1].lower() == "on"
    set_group_setting(message.chat.id, "captcha", enable)
    await message.reply_text(
        f"Captcha verification is now {'✅ ON' if enable else '❌ OFF'}\n"
        + ("New members will be muted until they verify they're human." if enable else "")
    )


@Client.on_message(filters.new_chat_members & filters.group, group=2)
async def start_captcha(client, message: Message):
    try:
        settings = get_group_settings(message.chat.id)
        if not settings.get("captcha"):
            return

        me = await client.get_me()
        for member in message.new_chat_members:
            if member.id == me.id:
                continue  # don't captcha-challenge the bot itself
            await _challenge_member(client, message.chat.id, member)
    except Exception as e:
        logger.warning(f"captcha start error: {e}")


async def _challenge_member(client: Client, chat_id: int, member):
    try:
        await client.restrict_chat_member(chat_id, member.id, permissions=MUTE_PERMS)
    except Exception as e:
        # If we can't mute (missing permission), skip the captcha entirely
        # rather than risk locking a real user out with no way to verify.
        logger.warning(f"captcha mute failed, skipping challenge: {e}")
        return

    btn = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ I'm not a robot", callback_data=f"captcha_ok:{member.id}")]]
    )
    sent = await client.send_message(
        chat_id,
        f"👋 {member.mention}, please verify you're human within {CAPTCHA_TIMEOUT} "
        f"seconds by tapping the button below, or you'll be removed.",
        reply_markup=btn,
    )
    _pending[(chat_id, member.id)] = sent.id
    asyncio.create_task(_captcha_timeout(client, chat_id, member.id, sent.id))


async def _captcha_timeout(client: Client, chat_id: int, user_id: int, prompt_msg_id: int):
    await asyncio.sleep(CAPTCHA_TIMEOUT)

    if _pending.get((chat_id, user_id)) != prompt_msg_id:
        return  # already solved (or superseded) - nothing to do

    _pending.pop((chat_id, user_id), None)
    try:
        await client.ban_chat_member(chat_id, user_id)
        await client.unban_chat_member(chat_id, user_id)  # ban+unban = kick, not permanent
    except Exception as e:
        logger.warning(f"captcha auto-kick failed: {e}")
    try:
        await client.delete_messages(chat_id, prompt_msg_id)
    except Exception:
        pass


@Client.on_callback_query(filters.regex(r"^captcha_ok:(\d+)$"))
async def solve_captcha(client: Client, callback_query: CallbackQuery):
    target_id = int(callback_query.matches[0].group(1))

    if callback_query.from_user.id != target_id:
        return await callback_query.answer("This captcha isn't for you.", show_alert=True)

    chat_id = callback_query.message.chat.id
    key = (chat_id, target_id)
    if key not in _pending:
        return await callback_query.answer("This captcha has expired.", show_alert=True)

    _pending.pop(key, None)
    try:
        await client.restrict_chat_member(chat_id, target_id, permissions=FULL_PERMS)
    except Exception as e:
        logger.warning(f"captcha unmute failed: {e}")

    await callback_query.answer("✅ Verified!")
    try:
        await callback_query.message.edit_text("✅ Verified! Welcome to the group.")
    except Exception:
        pass
