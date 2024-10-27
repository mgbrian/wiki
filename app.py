import os

from quart import Quart

# This has been moved here, and routes split into routes.py and sockets.py
# to allow sending socket messages/broadcasts from different parts of the
# app (outside of routes.py).
app = Quart(__name__)
import routes
import sockets


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000,
    )
