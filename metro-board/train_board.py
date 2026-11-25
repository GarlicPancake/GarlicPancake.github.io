# train_board.py  (BUILD_ID: MP4-64x32-ALIGNED-DOT1-NOFLICKER)
import terminalio
import displayio
from adafruit_display_text import bitmap_label


class TrainBoard:
    def __init__(self, display, cfg):
        self.display = display
        self.cfg = cfg

        self.group = displayio.Group()

        # ---- Background (static) ----
        bg = displayio.Bitmap(display.width, display.height, 1)
        pal = displayio.Palette(1)
        pal[0] = int(cfg.get("bg_color", 0x000000))
        self.group.append(displayio.TileGrid(bg, pixel_shader=pal))

        # ---- Colors ----
        self.dest_color = int(cfg.get("dest_color", 0xFFFFFF))
        self.min_color = int(cfg.get("min_color", 0xFFFFFF))

        # ---- Destination shortening ----
        self.dest_max = int(cfg.get("dest_max_chars", 10))
        self.alias = cfg.get("dest_alias", {}) or {}

        # ---- 1x1 status dot (top-right) ----
        self.dot_ok_color = 0x00FF00
        self.dot_bad_color = 0xFF0000
        self.dot_palette = displayio.Palette(1)
        self.dot_palette[0] = self.dot_bad_color  # start red until first success

        dot_bmp = displayio.Bitmap(1, 1, 1)
        self.dot = displayio.TileGrid(
            dot_bmp,
            pixel_shader=self.dot_palette,
            x=display.width - 1,
            y=0
        )
        self.group.append(self.dot)
        self._dot_state = None  # "ok" or "bad"

        # ---- Labels (3 rows) ----
        # Tuned for 64x32, terminalio font
        self.rows_y = [2, 12, 22]
        self.dest_x = 0
        self.min_x = display.width - 1  # right edge

        self.dest_labels = []
        self.min_labels = []

        for i in range(3):
            y = self.rows_y[i]

            d = bitmap_label.Label(
                terminalio.FONT,
                text="",
                color=self.dest_color,
                anchor_point=(0.0, 0.0),
                anchored_position=(self.dest_x, y),
            )

            m = bitmap_label.Label(
                terminalio.FONT,
                text="",
                color=self.min_color,
                anchor_point=(1.0, 0.0),
                anchored_position=(self.min_x, y),
            )

            self.group.append(d)
            self.group.append(m)

            self.dest_labels.append(d)
            self.min_labels.append(m)

        # Set once (prevents flicker)
        try:
            self.display.root_group = self.group
        except Exception:
            self.display.show(self.group)

    # ---- Dot control ----
    def set_dot_ok(self, ok: bool):
        state = "ok" if ok else "bad"
        if state == self._dot_state:
            return
        self._dot_state = state
        self.dot_palette[0] = self.dot_ok_color if ok else self.dot_bad_color

    # ---- Formatting ----
    def _short_dest(self, s):
        s = (s or "").strip()
        if s in self.alias:
            s = self.alias[s]
        if len(s) > self.dest_max:
            s = s[: self.dest_max]  # hard cut, no "..."
        return s

    @staticmethod
    def _min_text(v):
        s = str(v or "--").strip().upper()
        if s in ("ARR", "BRD", "DLY", "--"):
            return s
        try:
            n = int(s)
            if n <= 0:
                return "ARR"
            return str(n)
        except Exception:
            return "--"

    @staticmethod
    def _set_text_if_changed(label, new_text):
        # >>> FLICKER FIX #3: avoid rewriting identical text
        if label.text != new_text:
            label.text = new_text

    # ---- Rendering ----
    def show_trains(self, trains):
        trains = trains or []

        # Pack upward cleanly
        for i in range(3):
            if i < len(trains):
                t = trains[i]
                dest = self._short_dest(t.get("DestinationName") or t.get("Destination") or "")
                mins = self._min_text(t.get("Min", "--"))

                self._set_text_if_changed(self.dest_labels[i], dest)
                self._set_text_if_changed(self.min_labels[i], mins)
            else:
                self._set_text_if_changed(self.dest_labels[i], "")
                self._set_text_if_changed(self.min_labels[i], "")