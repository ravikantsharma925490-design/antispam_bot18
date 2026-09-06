from threading import Thread

from flask import Flask
from waitress import serve

import config

_app = Flask(__name__)


@_app.route("/")
def home():
    return "Anti-Spam bot is alive!"


def _run():
    # waitress is a production-grade WSGI server (unlike Flask's built-in
    # dev server), so no "development server" warning and it's safe to run
    # like this in a background thread alongside the bot.
    serve(_app, host="0.0.0.0", port=config.PORT)


def keep_alive():
    """Starts a tiny web server in a background thread so hosts that require
    a listening port (e.g. Render's free Web Service tier) treat this as a
    valid service instead of sleeping/rejecting it."""
    thread = Thread(target=_run, daemon=True)
    thread.start()
