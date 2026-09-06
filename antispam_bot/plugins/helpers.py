from pyrogram import Client, enums
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton

import config


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """True if user is a bot-level admin (config.ADMINS) or a group admin/owner."""
    if user_id in config.ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.ADMINISTRATOR,
            enums.ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def get_missing_join_buttons(client: Client, user_id: int) -> list:
    """
    Checks config.AUTH_CHANNELS + config.AUTH_GROUPS for membership.
    Returns a list of InlineKeyboardButton (one per chat the user hasn't
    joined yet), each linking to an invite link. Empty list means the user
    has joined everything required (or nothing is configured).
    """
    required = config.AUTH_CHANNELS + config.AUTH_GROUPS
    if not required:
        return []

    buttons = []
    for chat_id in required:
        try:
            await client.get_chat_member(chat_id, user_id)
            continue  # already a member, nothing to show
        except UserNotParticipant:
            pass
        except Exception:
            continue  # can't check this one (bad ID / bot not admin) - skip silently

        try:
            chat = await client.get_chat(chat_id)
            invite_link = await client.create_chat_invite_link(chat_id)
            label = (
                f"👥 Join {chat.title}"
                if chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP)
                else f"📢 Join {chat.title}"
            )
            buttons.append(InlineKeyboardButton(label, url=invite_link.invite_link))
        except Exception:
            continue  # couldn't create an invite link - skip this one

    return buttons
