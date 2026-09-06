# Anti-Spam Telegram Bot

A lightweight Telegram group moderation bot built with Pyrogram. No database
required — settings are stored in a local `settings.json` file.

## Features

- `/antilink on|off` — deletes links / `@usernames` sent by non-admin members
- `/antiflood on|off` — auto-mutes a member who sends too many messages too fast
- `/setflood <count> <seconds>` — customize the flood threshold per group
- `/badwords on|off`, `/addword`, `/removeword`, `/wordlist` — custom bad-word filter
- `/warn`, `/warns`, `/resetwarns` — warning system, auto-bans at 3 warns
- `/ban`, `/unban`, `/kick`, `/mute`, `/unmute` — moderation commands (reply to a user)
- `/welcome on|off`, `/welcome set <message>` — greet new members with a photo background (default ON)
- `/welcome setimage` (reply to a photo), `/welcome resetimage` — customize the welcome image
- `/goodbye on|off` — announce when someone leaves (default OFF)
- `/captcha on|off` — mute new members until they tap a "not a robot" button; auto-kicks them if they don't verify within 60 seconds (great for blocking spam bots)
- **Force-Subscribe**: require users to join specific channel(s)/group(s) before using the bot in private chat (see `AUTH_CHANNELS` / `AUTH_GROUPS` below)
- `/report [reason]` (reply to a message) — flags it to admins with quick Mute/Ban/Dismiss buttons; deletes the reported message automatically
- `/settings` — view the current settings for a group
- On startup, the bot sends a "✅ I'm online" message to everyone listed in `ADMINS`
- Sends a message to `LOG_CHANNEL` whenever the bot is added to or removed from a group

## Setup

1. Get `API_ID` and `API_HASH` from https://my.telegram.org
2. Get a `BOT_TOKEN` from [@BotFather](https://t.me/BotFather)
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set environment variables (see below), then run:
   ```
   python3 bot.py
   ```

## Environment Variables

| Variable        | Required | Description                                              |
|-----------------|----------|------------------------------------------------------------|
| `API_ID`        | Yes      | From my.telegram.org                                       |
| `API_HASH`      | Yes      | From my.telegram.org                                        |
| `BOT_TOKEN`     | Yes      | From @BotFather                                             |
| `ADMINS`        | No       | Space-separated Telegram user IDs treated as bot admins everywhere; also receive a "bot is online" DM on startup |
| `FLOOD_LIMIT`   | No       | Default max messages before mute (default: 5)               |
| `FLOOD_SECONDS` | No       | Default time window in seconds (default: 10)                |
| `DATA_FILE`     | No       | Path to the JSON settings file (default: `settings.json`)   |
| `WELCOME_IMG`   | No       | Default image URL shown in welcome messages (each group can override this with `/welcome setimage`) |
| `LOG_CHANNEL`   | No       | Channel ID where "added to a new group" / "removed from a group" notifications are posted (bot must be admin there) |
| `AUTH_CHANNELS` | No       | Space-separated channel IDs users must join before using the bot in PM (bot must be admin in each) |
| `AUTH_GROUPS`   | No       | Space-separated group IDs users must join before using the bot in PM (bot must be admin in each) |

**Note:** for the startup DM to reach an admin, that admin must have sent
`/start` to the bot at least once before (Telegram bots can't message a user
who has never opened a chat with them).

Add the bot to your group as an **Admin** with:
- ✅ Delete messages
- ✅ Restrict members (ban/mute users) — needed for mute, ban, kick, anti-flood

## Deploying on Render (Free Tier)

Render's free tier only supports **Web Services** (not Background Workers), so
this project includes a tiny built-in web server (`keep_alive.py`) that
satisfies that requirement - Render will see it as a normal web app.

1. Push this project to a GitHub repo
2. On Render, create a new **Web Service** (not a Background Worker)
3. Set the environment variables above (Render sets `PORT` automatically -
   you don't need to add it yourself)
4. Deploy — Render will run `python3 bot.py` via the Procfile

**Important caveats of the free tier:**
- Render's free Web Services **sleep after ~15 minutes of no HTTP traffic**,
  and **restart periodically**. Every restart wipes the in-memory state
  (e.g. flood counters) and, since Render's free disk is not persistent,
  can also wipe `settings.json` (group settings) unless you use an external
  database instead.
- To reduce sleeping, use a free uptime pinger (e.g. UptimeRobot) to ping
  your Render URL every 5–10 minutes. This does **not** guarantee 24/7
  uptime on the free tier, but it helps significantly.
- For guaranteed persistence and uptime, a small paid plan (Background
  Worker or a paid Web Service with a persistent disk) is more reliable.

If you don't mind paying a small amount for reliability, a **Background
Worker** (`worker: python3 bot.py` in the Procfile, no `keep_alive.py`
needed) is the more "correct" way to run this kind of bot long-term.

## Commands Usage

In your group:
```
/antilink on
/antiflood on
/setflood 5 10
/settings
```
