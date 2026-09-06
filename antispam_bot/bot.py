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
 
    # Notify the log channel that the bot is online (instead of DMing admins)
    if config.LOG_CHANNEL:
        try:
            await app.send_message(
                config.LOG_CHANNEL,
                f"✅ <b>{me.first_name}</b> is now online and protecting your groups!\n\n"
                f"Username: @{me.username}",
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception as e:
            print(f"⚠️ Couldn't send startup message to LOG_CHANNEL: {e}")
 
    await idle()
    await app.stop()
 
 
if __name__ == "__main__":
    keep_alive()
    print("🚀 Anti-Spam Bot is starting...")
    asyncio.get_event_loop().run_until_complete(main())
 
