import os
import pickle
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from pyblinky import AsyncWemo
from starlette.datastructures import State

from src.constants import IR_CODES, Environment
from src.devices import Chromecast, Remote, RemoteButton

ENVIRONMENT = Environment(os.environ["ENVIRONMENT"])
SENTRY_DSN = os.environ.get("SENTRY_DSN")

PUBLIC_GATEWAY_IP = "192.168.50.1"

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

CHROMECAST_IP = "192.168.50.236"
CHROMECAST_PORT = 8009

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


class AppState(State):
    plugs: list[AsyncWemo]
    remote: Remote
    chromecast: Chromecast


class TarantulaApp(FastAPI):
    state: AppState


@asynccontextmanager
async def lifespan(app: TarantulaApp) -> AsyncGenerator:
    app.state.plugs = []
    with open(os.environ["DYNAMIC_CONFIG_FILENAME"], "rb") as f:
        dynamic_config: dict = pickle.load(f)
        app.state.plugs = dynamic_config["plugs"]
        app.state.remote = dynamic_config["remote"]

    # must be done in app context due to threading
    app.state.chromecast = Chromecast(CHROMECAST_IP, CHROMECAST_PORT)
    yield
