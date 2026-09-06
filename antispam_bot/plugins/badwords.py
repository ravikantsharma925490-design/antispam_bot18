import logging
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from storage import get_group_settings, set_group_setting
from .helpers import is_admin

logger = logging.getLogger(__name__)

# Default list is intentionally minimal - admins add their own words with /addword.
DEFAULT_BAD_WORDS = set()


def _compile_pattern(words):
    if not words:
        return None
    escaped = [re.escape(w) for w in words]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


@Client.on_message(filters.command("badwords") & filters.group)
async def toggle_badwords(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split()
    if len(args) != 2 or args[1].lower() not in ("on", "off"):
        return await message.reply_text(
            "Usage:\n<code>/badwords on</code>\n<code>/badwords off</code>"
        )

    enable = args[1].lower() == "on"
    set_group_setting(message.chat.id, "badwords", enable)
    await message.reply_text(f"Bad-word filter is now {'✅ ON' if enable else '❌ OFF'}")


@Client.on_message(filters.command("addword") & filters.group)
async def add_bad_word(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        return await message.reply_text("Usage: /addword <word>")

    word = args[1].strip().lower()
    settings = get_group_settings(message.chat.id)
    words = set(settings.get("bad_word_list", []))
    words.add(word)
    set_group_setting(message.chat.id, "bad_word_list", sorted(words))
    await message.reply_text(f"✅ Added \"{word}\" to the bad-word list.")


@Client.on_message(filters.command("removeword") & filters.group)
async def remove_bad_word(client, message: Message):
    if not message.from_user:
        return await message.reply_text("Anonymous admins can't use this command.")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("⚠️ Only group admins can use this command.")

    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        return await message.reply_text("Usage: /removeword <word>")

    word = args[1].strip().lower()
    settings = get_group_settings(message.chat.id)
    words = set(settings.get("bad_word_list", []))
    words.discard(word)
    set_group_setting(message.chat.id, "bad_word_list", sorted(words))
    await message.reply_text(f"✅ Removed \"{word}\" from the bad-word list.")


@Client.on_message(filters.command("wordlist") & filters.group)
async def show_word_list(client, message: Message):
    settings = get_group_settings(message.chat.id)
    words = settings.get("bad_word_list", [])
    if not words:
        return await message.reply_text("No bad words configured yet. Add one with /addword <word>.")
    await message.reply_text("<b>🚫 Bad words:</b>\n" + ", ".join(words))


@Client.on_message(filters.group & filters.text & filters.incoming, group=7)
async def filter_bad_words(client, message: Message):
    try:
        if not message.from_user:
            return

        settings = get_group_settings(message.chat.id)
        if not settings.get("badwords"):
            return

        words = settings.get("bad_word_list", [])
        pattern = _compile_pattern(words)
        if not pattern or not pattern.search(message.text or ""):
            return

        if await is_admin(client, message.chat.id, message.from_user.id):
            return

        chat_id = message.chat.id
        mention = message.from_user.mention

        await message.delete()
        warn = await client.send_message(
            chat_id, f"🚫 {mention}, that word isn't allowed here."
        )
        await asyncio_sleep_and_delete(warn)
    except Exception as e:
        logger.warning(f"badwords filter error: {e}")


async def asyncio_sleep_and_delete(msg: Message, delay: int = 6):
    import asyncio

    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass
