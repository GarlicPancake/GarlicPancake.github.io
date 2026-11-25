# config.py

config = {
    "proxy_base_url": "http://XXX:5050",
    "metro_station_code": "D02",
    "train_group": "2",

    "max_trains": 3,
    "refresh_seconds": 15,
    "hold_last_good_seconds": 70,

    # >>> FLICKER FIX #1 (biggest): lower brightness to reduce current spikes
    # try 0.10–0.25 (lower = steadier)
    "display_brightness": 0.15,

    "bg_color": 0x000000,
    "dest_color": 0x6E8B3D,
    "min_color": 0xFFFFFF,

    "dest_max_chars": 10,
    "dest_alias": {
        "Franconia-Springfield": "FRANCON",
        "Vienna/Fairfax-GMU": "VIENNA",
    },
}