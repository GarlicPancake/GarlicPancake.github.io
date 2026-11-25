# metro_api.py  (BUILD_ID: MP4-REQUESTS-GUARD)
import time

class MetroApiError(Exception):
    pass

class MetroApi:
    def __init__(self, portal, cfg):
        self.portal = portal
        self.cfg = cfg

        base = str(cfg.get("proxy_base_url", "")).rstrip("/")
        if not base:
            raise MetroApiError("proxy_base_url is blank in config.py")
        self.url = f"{base}/wmata/{cfg.get('metro_station_code','D02')}?group={cfg.get('train_group','2')}"

        self.max_trains = int(cfg.get("max_trains", 3))
        self.hold_last = int(cfg.get("hold_last_good_seconds", 70))

        self._last_good = None
        self._last_good_t = 0.0

        # Make sure MatrixPortal network is connected AND requests exists
        self._ensure_connected()

    def _ensure_connected(self):
        # Try to connect using MatrixPortal's built-in network stack.
        try:
            # Many builds have this method
            if hasattr(self.portal, "network") and hasattr(self.portal.network, "connect"):
                self.portal.network.connect()
        except Exception as e:
            # It's okay if it's already connected; we only care about usable requests.
            print("WiFi connect attempt:", repr(e))

        # Validate requests object
        req = None
        if hasattr(self.portal, "network") and hasattr(self.portal.network, "requests"):
            req = self.portal.network.requests

        if req is None:
            raise MetroApiError(
                "matrixportal.network.requests is None.\n"
                "Fix: copy these from the *same* CircuitPython 10.x bundle into /lib:\n"
                "  - adafruit_requests.mpy\n"
                "  - adafruit_connection_manager.mpy (if present in your bundle)\n"
                "  - plus your matrixportal/portalbase libs\n"
            )

        self.requests = req

    @staticmethod
    def _eta_sort_key(mins):
        s = str(mins).strip().upper()
        if s == "BRD":
            return (0, 0)
        if s == "ARR":
            return (1, 0)
        if s == "DLY":
            return (3, 0)
        try:
            return (2, int(s))
        except Exception:
            return (4, 0)

    def get_trains(self):
        now = time.monotonic()
        print("MetroApi GET:", self.url)

        try:
            r = self.requests.get(self.url, timeout=10)
            try:
                data = r.json()
            finally:
                try:
                    r.close()
                except Exception:
                    pass

            if not isinstance(data, dict):
                raise MetroApiError("Response not JSON dict")

            trains = data.get("Trains", [])
            if not isinstance(trains, list):
                raise MetroApiError("JSON missing Trains list")

            trains = sorted(trains, key=lambda t: self._eta_sort_key(t.get("Min", "--")))
            trains = trains[: self.max_trains]

            self._last_good = trains
            self._last_good_t = now
            return trains, False  # False = not cached

        except Exception as e:
            if self._last_good is not None and (now - self._last_good_t) <= self.hold_last:
                print("MetroApi WARN: using cached:", repr(e))
                return self._last_good, True  # True = cached
            raise MetroApiError(f"Request failed: {repr(e)}")