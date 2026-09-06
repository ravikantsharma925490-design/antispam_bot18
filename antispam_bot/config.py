import os

# Get these from https://my.telegram.org
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")

# Get this from @BotFather
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Space-separated Telegram user IDs who are always treated as bot admins
# (bypass antilink/antiflood everywhere, regardless of group admin status)
ADMINS = [
    int(x) for x in os.environ.get("ADMINS", "").split() if x.strip().isdigit()
]

# Default flood settings (used until a group sets its own with /setflood)
FLOOD_LIMIT = int(os.environ.get("FLOOD_LIMIT", "5"))     # max messages
FLOOD_SECONDS = int(os.environ.get("FLOOD_SECONDS", "10"))  # time window in seconds

# Where per-group settings are persisted (JSON file, no database needed)
DATA_FILE = os.environ.get("DATA_FILE", "settings.json")

# Port for the keep-alive web server (required so Render's free "Web Service"
# tier accepts this as a valid service - it needs something listening on a port)
PORT = int(os.environ.get("PORT", "8080"))

# Default welcome image shown to new members (can be overridden per group
# with /welcome setimage, by replying to a photo)
WELCOME_IMG = os.environ.get(
    "WELCOME_IMG",
    "https://graph.org/file/56b5deb73f3b132e2bb73.jpg",
)

# Channel where the bot posts "added to a new group" / "removed from a group"
# notifications. Must be a channel where the bot is an admin. Leave unset to
# disable this feature.
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0")) or None

# Force-subscribe: space-separated channel/group IDs that a user must join
# before they can use the bot in private chat (e.g. /start). The bot must be
# an admin in each one (needed to check membership and generate invite links).
# Leave both empty/unset to disable this feature entirely.
AUTH_CHANNELS = [
    int(x) for x in os.environ.get("AUTH_CHANNELS", "").split() if x.lstrip("-").isdigit()
]
AUTH_GROUPS = [
    int(x) for x in os.environ.get("AUTH_GROUPS", "").split() if x.lstrip("-").isdigit()
]
