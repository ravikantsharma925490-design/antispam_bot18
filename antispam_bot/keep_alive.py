from threading import Thread

from flask import Flask

import config

_app = Flask(__name__)


@_app.route("/")
def home():
    return "Anti-Spam bot is alive!"


def _run():
    # use_reloader=False is important - without it Flask tries to spawn a
    # second process which breaks things when run inside a thread.
    _app.run(host="0.0.0.0", port=config.PORT, use_reloader=False)


def keep_alive():
    """Starts a tiny web server in a background thread so hosts that require
    a listening port (e.g. Render's free Web Service tier) treat this as a
    valid service instead of sleeping/rejecting it."""
    thread = Thread(target=_run, daemon=True)
    thread.start()
