import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from pyblinky import AsyncWemo

from src.constants import IR_CODES, Environment
from src.devices import Remote, RemoteButton

ENVIRONMENT = Environment(os.environ["ENVIRONMENT"])
SENTRY_DSN = os.environ.get("SENTRY_DSN")

# network location of plugs
PLUG_IPS = (
    "192.168.50.100",
    "192.168.50.196",
    "192.168.50.190",
    "192.168.50.199",
    "192.168.50.178",
    "192.168.50.242",
    "192.168.50.200",
)

# time in seconds to cache plug name
PLUG_CACHE_NAME_TIME = 31536000

# time in seconds to cache static files in browser
STATIC_CACHE_TIME = int(os.environ.get("STATIC_CACHE_TIME", 31536000))

# unique key to bust cache on updates
STATIC_CACHE_KEY = os.environ.get("STATIC_CACHE_KEY")

# caching on, and key not set, don't start up
if STATIC_CACHE_TIME > 0 and not STATIC_CACHE_KEY:
    raise Exception("Invalid static cache configuration")

# infared emitter by tv
IR_EMITTER_IP = "192.168.50.96"

# ir remote configuration
REMOTE_BUTTONS = [
    RemoteButton("power", [IR_CODES["tv"]["power"], IR_CODES["speaker"]["power"]]),
    RemoteButton("source", [IR_CODES["tv"]["source"]]),
    RemoteButton("➕ 🔊", [IR_CODES["speaker"]["vol_up"]]),
    RemoteButton("➖ 🔉", [IR_CODES["speaker"]["vol_down"]]),
    RemoteButton("1 - chromecast", [IR_CODES["hdmi_switch"]["1"]]),
    RemoteButton("2 - retropie", [IR_CODES["hdmi_switch"]["2"]]),
    RemoteButton("3 - N64", [IR_CODES["hdmi_switch"]["3"]]),
    RemoteButton("4 - streamer", [IR_CODES["hdmi_switch"]["4"]]),
    RemoteButton("5 - googletv", [IR_CODES["hdmi_switch"]["5"]]),
    RemoteButton("🔇", [IR_CODES["speaker"]["mute"]]),
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    app.state.plugs = [
        AsyncWemo(ip, name_cache_age=PLUG_CACHE_NAME_TIME)
        for ip in os.environ["ACTIVE_PLUG_IPS"].split(",")
    ]
    app.state.remote = Remote(IR_EMITTER_IP, REMOTE_BUTTONS)
    yield
