import base64
import time
import uuid
from datetime import datetime
from enum import Enum

import broadlink
import pychromecast
from pydantic import BaseModel


class ChromecastPlaybackStatus(Enum):
    PLAYING = pychromecast.controllers.media.MEDIA_PLAYER_STATE_PLAYING
    BUFFERING = pychromecast.controllers.media.MEDIA_PLAYER_STATE_BUFFERING
    PAUSED = pychromecast.controllers.media.MEDIA_PLAYER_STATE_PAUSED
    IDLE = pychromecast.controllers.media.MEDIA_PLAYER_STATE_IDLE
    UNKNOWN = pychromecast.controllers.media.MEDIA_PLAYER_STATE_UNKNOWN


class ChromecastState(BaseModel):
    playback_status: ChromecastPlaybackStatus
    duration: float | None
    current_time: float | None
    title: str | None
    last_updated: datetime | None


class ChromecastRequestNotAllowed(Exception):
    pass


class Chromecast:
    device: pychromecast.Chromecast

    def __init__(
        self, ip: str, port: int = 8009, device_id: uuid.UUID | None = None
    ) -> None:
        if not device_id:
            device_id = uuid.uuid4()
        self.device = pychromecast.get_chromecast_from_host(
            (ip, port, device_id, str(device_id), str(device_id))
        )
        self.device.wait()

    def get_state(self) -> ChromecastState:
        mc = self.device.media_controller
        mc.update_status()
        return ChromecastState(
            playback_status=ChromecastPlaybackStatus[mc.status.player_state],
            duration=mc.status.duration,
            current_time=mc.status.current_time if mc.status.duration else None,
            title=mc.status.title,
            last_updated=mc.status.last_updated,
        )

    def start(self, url: str, mime_type: str) -> ChromecastState:
        self.device.media_controller.play_media(url, mime_type)
        return self._wait_for_playback_status(
            [ChromecastPlaybackStatus.PLAYING, ChromecastPlaybackStatus.BUFFERING]
        )

    def pause(self) -> ChromecastState:
        try:
            self.device.media_controller.pause()
        except pychromecast.error.RequestFailed as e:
            raise ChromecastRequestNotAllowed() from e
        return self._wait_for_playback_status([ChromecastPlaybackStatus.PAUSED])

    def play(self) -> ChromecastState:
        try:
            self.device.media_controller.play()
        except pychromecast.error.RequestFailed as e:
            raise ChromecastRequestNotAllowed() from e
        return self._wait_for_playback_status([ChromecastPlaybackStatus.PLAYING])

    def seek(self, time: int) -> ChromecastState:
        try:
            self.device.media_controller.seek(time)
        except pychromecast.error.RequestFailed as e:
            raise ChromecastRequestNotAllowed() from e
        return self._wait_for_playback_status([ChromecastPlaybackStatus.PLAYING])

    def stop(self) -> None:
        try:
            self.device.media_controller.stop()
        except pychromecast.error.RequestFailed:
            pass
        self.device.quit_app()

    def _wait_for_playback_status(
        self, statuses: list[ChromecastPlaybackStatus], interval: int = 1
    ) -> ChromecastState:
        while True:
            state = self.get_state()
            if state.playback_status in statuses:
                return state
            time.sleep(interval)


class Emitter:
    ip: str
    timeout: int
    device: broadlink.Device

    def __init__(self, ip: str, timeout: int = 30):
        self.ip = ip
        self.timeout = timeout
        self.device = None

    def reset(self) -> None:
        self.device = broadlink.hello(self.ip, timeout=self.timeout)
        self.device.timeout = self.timeout
        self.device.auth()

    def send_data(self, code: bytes) -> None:
        if not self.device:
            self.reset()
        if self.device:
            self.device.send_data(code)

    """
    Custom logic is needed because broadlink.Device objects cannot be pickled
    """

    def __getstate__(self) -> dict:
        data = {
            attr: getattr(self, attr) for attr in dir(self) if not attr.startswith("__")
        }
        if self.device is not None:
            data["device"] = {
                "id": self.device.id,
                "timeout": self.timeout,
                "host": self.device.host,
                "mac": self.device.mac,
                "devtype": self.device.devtype,
                "aes": self.device.aes,
                "__class__": type(self.device),
            }
        return data

    def __setstate__(self, state: dict) -> None:
        for k, v in state.items():
            if k != "device":
                setattr(self, k, v)
        self.device = None
        if state["device"] is not None:
            self.device = state["device"]["__class__"](
                state["device"]["host"],
                state["device"]["mac"],
                state["device"]["devtype"],
            )
            self.device.aes = state["device"]["aes"]
            self.device.id = state["device"]["id"]
            self.device.timeout = state["device"]["timeout"]


class RemoteButton:
    def __init__(self, name: str, codes: list[str]):
        self.name = name
        self.codes = codes


class Remote:
    def __init__(self, ip: str, buttons: list[RemoteButton]):
        self.emitter = Emitter(ip)
        self.buttons = buttons
        try:
            self.emitter.reset()
        except Exception:
            pass

    def press_button(self, index: int) -> None:
        for code in self.buttons[index].codes:
            self.emitter.send_data(base64.b64decode(code))
