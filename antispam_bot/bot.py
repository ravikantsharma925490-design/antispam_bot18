import asyncio

from pyrogram import Client, enums, idle

import config
from keep_alive import keep_alive

app = Client(
    "antispam_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="plugins"),
)


async def main():
    await app.start()
    me = await app.get_me()
    print(f"🚀 {me.first_name} (@{me.username}) started successfully!")

    # Notify configured admins that the bot is online
    for admin_id in config.ADMINS:
        try:
            await app.send_message(
                admin_id,
                f"✅ <b>{me.first_name}</b> is now online and protecting your groups!\n\n"
                f"Username: @{me.username}",
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass  # admin may not have started a DM with the bot yet

    await idle()
    await app.stop()


if __name__ == "__main__":
    keep_alive()
    print("🚀 Anti-Spam Bot is starting...")
    asyncio.get_event_loop().run_until_complete(main())
