# code.py  (BUILD_ID: MP4-ONE-PORTAL-DOT1-NOFLICKER)
import time
from adafruit_matrixportal.matrixportal import MatrixPortal

from config import config
from metro_api import MetroApi, MetroApiError
from train_board import TrainBoard

print("Starting MatrixPortal Train Board...")

# Create MatrixPortal ONCE (prevents ESP_BUSY)
portal = MatrixPortal(status_neopixel=None, debug=False)

# >>> FLICKER FIX #1: lower brightness (reduces current spikes)
try:
    portal.display.brightness = float(config.get("display_brightness", 0.15))
except Exception:
    pass

board = TrainBoard(portal.display, config)
api = MetroApi(portal, config)

refresh = int(config.get("refresh_seconds", 15))

while True:
    try:
        trains, used_cache = api.get_trains()

        # Dot logic: green only for LIVE WMATA receive, red if cached/failure
        board.set_dot_ok(ok=(not used_cache))

        # Update rows (does NOT rebuild screen)
        board.show_trains(trains)

    except MetroApiError as e:
        print("MetroApiError:", repr(e))
        # >>> FLICKER FIX #2: freeze screen, just make dot red
        board.set_dot_ok(False)

    except Exception as e:
        print("ERROR:", repr(e))
        board.set_dot_ok(False)

    time.sleep(refresh)