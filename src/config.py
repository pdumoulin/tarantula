"""Static application configs."""

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from pyblinky import AsyncWemo

from src.constants import IR_CODES
from src.devices import Remote
from src.devices import RemoteButton

# network location of plugs
PLUG_IPS = (
    '192.168.50.100',
    '192.168.50.196',
    '192.168.50.190',
    '192.168.50.199',
    '192.168.50.178',
    '192.168.50.242',
    '192.168.50.200'
)

# time in seconds to cache plug name
PLUG_CACHE_NAME_TIME = 60 * 60 * 24

# time in seconds to cache static files in browser
STATIC_CACHE_TIME = int(os.environ.get('STATIC_CACHE_TIME', 3600))

# infared emitter by tv
IR_EMITTER_IP = '192.168.50.96'

# ir remote configuration
REMOTE_BUTTONS = [
    RemoteButton(
        'power',
        [IR_CODES['tv']['power'], IR_CODES['speaker']['power']]),
    RemoteButton(
        'source',
        [IR_CODES['tv']['source']]),
    RemoteButton(
        'vol up',
        [IR_CODES['speaker']['vol_up']]),
    RemoteButton(
        'vol down',
        [IR_CODES['speaker']['vol_down']]),
    RemoteButton(
        '1 - chromecast',
        [IR_CODES['hdmi_switch']['1']]),
    RemoteButton(
        '2 - retropie',
        [IR_CODES['hdmi_switch']['2']]),
    RemoteButton(
        '3 - N64',
        [IR_CODES['hdmi_switch']['3']]),
    RemoteButton(
        '4 - streamer',
        [IR_CODES['hdmi_switch']['4']]),
    RemoteButton(
        '5 - googletv',
        [IR_CODES['hdmi_switch']['5']]),
    RemoteButton(
        'mute',
        [IR_CODES['speaker']['mute']]),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize objects used cross request for lifetime of app."""
    all_plugs = [
        AsyncWemo(x, name_cache_age=PLUG_CACHE_NAME_TIME)
        for x in PLUG_IPS
    ]
    results = await asyncio.gather(
        *[
            y.identify()
            for y in all_plugs
        ],
        return_exceptions=True
    )
    app.state.plugs = [
        plug if not isinstance(result, Exception) else False
        for plug, result in zip(all_plugs, results)
    ]
    app.state.remote = Remote(IR_EMITTER_IP, REMOTE_BUTTONS)
    yield
