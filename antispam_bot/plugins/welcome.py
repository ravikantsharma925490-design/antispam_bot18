import logging

from pyrogram import Client, enums, filters
from pyrogram.types import Message

import config
from storage import get_group_settings, set_group_setting
from .helpers import is_admin

logger = logging.getLogger(__name__)

DEFAULT_WELCOME = "👋 Welcome {mention} to <b>{chat_title}</b>!\n\nPlease read the group rules and enjoy your stay 🎉"
DEFAULT_GOODBYE = "👋 {mention} has left {chat_title}."


@Client.on_message(filters.command("welcome") & filters.group)
async def toggle_welcome(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply_text(
            "Usage:\n"
            "<code>/welcome on</code>\n"
            "<code>/welcome off</code>\n"
            "<code>/welcome set &lt;message&gt;</code> — use {mention} and {chat_title} as placeholders\n"
            "<code>/welcome setimage</code> — reply to a photo to use it as the welcome background\n"
            "<code>/welcome resetimage</code> — go back to the default welcome image"
        )

    sub = args[1].split(maxsplit=1)
    action = sub[0].lower()

    if action == "on":
        set_group_setting(message.chat.id, "welcome", True)
        return await message.reply_text("✅ Welcome messages are now ON.")

    if action == "off":
        set_group_setting(message.chat.id, "welcome", False)
        return await message.reply_text("❌ Welcome messages are now OFF.")

    if action == "set" and len(sub) == 2:
        set_group_setting(message.chat.id, "welcome_text", sub[1])
        return await message.reply_text("✅ Custom welcome message saved.")

    if action == "setimage":
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await message.reply_text("Reply to a photo with /welcome setimage to set it.")
        file_id = message.reply_to_message.photo.file_id
        set_group_setting(message.chat.id, "welcome_img", file_id)
        return await message.reply_text("✅ Welcome image updated.")

    if action == "resetimage":
        set_group_setting(message.chat.id, "welcome_img", None)
        return await message.reply_text("✅ Welcome image reset to default.")

    await message.reply_text("Usage: /welcome on|off|set <message>|setimage|resetimage")


@Client.on_message(filters.new_chat_members & filters.group)
async def greet_new_member(client, message: Message):
    try:
        settings = get_group_settings(message.chat.id)
        if not settings.get("welcome", True):  # default ON
            return

        template = settings.get("welcome_text", DEFAULT_WELCOME)
        image = settings.get("welcome_img") or config.WELCOME_IMG
        me = await client.get_me()

        for member in message.new_chat_members:
            if member.id == me.id:
                continue  # don't greet the bot itself when it's added to a group
            caption = template.format(mention=member.mention, chat_title=message.chat.title)
            try:
                await client.send_photo(
                    message.chat.id,
                    photo=image,
                    caption=caption,
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception as e:
                # fall back to plain text if the image fails to send for any reason
                logger.warning(f"welcome image failed, sending text instead: {e}")
                await message.reply_text(caption)
    except Exception as e:
        logger.warning(f"welcome error: {e}")


@Client.on_message(filters.left_chat_member & filters.group)
async def announce_left_member(client, message: Message):
    try:
        settings = get_group_settings(message.chat.id)
        if not settings.get("goodbye", False):  # default OFF (less noisy)
            return
        member = message.left_chat_member
        if not member:
            return
        text = DEFAULT_GOODBYE.format(mention=member.mention, chat_title=message.chat.title)
        await message.reply_text(text)
    except Exception as e:
        logger.warning(f"goodbye error: {e}")


@Client.on_message(filters.command("goodbye") & filters.group)
async def toggle_goodbye(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split()
    if len(args) != 2 or args[1].lower() not in ("on", "off"):
        return await message.reply_text("Usage: /goodbye on | /goodbye off")

    enable = args[1].lower() == "on"
    set_group_setting(message.chat.id, "goodbye", enable)
    await message.reply_text(f"Goodbye messages are now {'✅ ON' if enable else '❌ OFF'}")
