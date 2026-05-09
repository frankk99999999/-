# -*- coding: utf-8 -*-
"""PyInstaller executable entry point for the campus trading platform."""

import threading
import time
import webbrowser

from app import app, db


def _open_browser():
    """Open homepage after server starts."""
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:12000")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=12000, debug=False, use_reloader=False)
