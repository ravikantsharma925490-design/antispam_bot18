import logging
import time

from pyrogram import Client, enums, filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from .helpers import is_admin

logger = logging.getLogger(__name__)

REPORT_COOLDOWN = 60  # seconds a single user must wait between reports in a group
_last_report = {}  # (chat_id, user_id) -> timestamp of last report

MUTE_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)


@Client.on_message(filters.command("report") & filters.group)
async def report_cmd(client: Client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")

    if not message.reply_to_message:
        return await message.reply_text("Reply to the message you want to report with /report.")

    if not message.reply_to_message.from_user:
        return await message.reply_text("Can't report this message.")

    reported_user = message.reply_to_message.from_user
    if reported_user.id == message.from_user.id:
        return await message.reply_text("You can't report your own message.")

    if await is_admin(client, message.chat.id, reported_user.id):
        return await message.reply_text("Can't report an admin.")

    # simple per-user cooldown to prevent report spam
    key = (message.chat.id, message.from_user.id)
    now = time.time()
    if now - _last_report.get(key, 0) < REPORT_COOLDOWN:
        return await message.reply_text("⏳ Please wait a bit before reporting again.")
    _last_report[key] = now

    reason = ""
    args = message.text.split(maxsplit=1)
    if len(args) == 2:
        reason = args[1]

    try:
        await message.reply_to_message.delete()
        deleted = True
    except Exception:
        deleted = False  # bot couldn't delete it yet, admins can still act on the report

    text = (
        f"🚨 <b>New Report</b>\n\n"
        f"<b>Reported user:</b> {reported_user.mention} (<code>{reported_user.id}</code>)\n"
        f"<b>Reported by:</b> {message.from_user.mention}\n"
    )
    if reason:
        text += f"<b>Reason:</b> {reason}\n"
    if deleted:
        text += "\n🗑 The reported message has already been deleted."

    buttons = [
        [
            InlineKeyboardButton("🔇 Mute", callback_data=f"report_mute:{reported_user.id}"),
            InlineKeyboardButton("🚫 Ban", callback_data=f"report_ban:{reported_user.id}"),
        ],
        [InlineKeyboardButton("✅ Dismiss", callback_data="report_dismiss")],
    ]

    await client.send_message(
        message.chat.id,
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML,
    )
    await message.reply_text("✅ Report sent to admins.")


@Client.on_callback_query(filters.regex(r"^report_(mute|ban):(\d+)$"))
async def handle_report_action(client: Client, callback_query: CallbackQuery):
    action, target_id_str = callback_query.matches[0].groups()
    target_id = int(target_id_str)
    chat_id = callback_query.message.chat.id

    if not await is_admin(client, chat_id, callback_query.from_user.id):
        return await callback_query.answer("⚠️ Only admins can act on reports.", show_alert=True)

    try:
        if action == "mute":
            await client.restrict_chat_member(chat_id, target_id, permissions=MUTE_PERMS)
            result_text = f"🔇 User has been muted by {callback_query.from_user.mention}."
        else:  # ban
            await client.ban_chat_member(chat_id, target_id)
            result_text = f"🚫 User has been banned by {callback_query.from_user.mention}."

        await callback_query.message.edit_text(
            callback_query.message.text.html + f"\n\n{result_text}",
            parse_mode=enums.ParseMode.HTML,
        )
        await callback_query.answer("Done.")
    except ChatAdminRequired:
        await callback_query.answer(
            "⚠️ I need admin rights with the right permissions to do this.", show_alert=True
        )
    except Exception as e:
        logger.warning(f"report action error: {e}")
        await callback_query.answer(f"⚠️ Couldn't complete action: {e}", show_alert=True)


@Client.on_callback_query(filters.regex("^report_dismiss$"))
async def dismiss_report(client: Client, callback_query: CallbackQuery):
    if not await is_admin(client, callback_query.message.chat.id, callback_query.from_user.id):
        return await callback_query.answer("⚠️ Only admins can dismiss reports.", show_alert=True)

    await callback_query.answer("Dismissed.")
    try:
        await callback_query.message.edit_text(
            callback_query.message.text.html + f"\n\n✅ Dismissed by {callback_query.from_user.mention}.",
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        pass
