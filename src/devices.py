"""IR emitters."""

import base64

import broadlink


class Emitter():
    """Wrapper class for IR device handling."""

    def __init__(self, ip: str):
        """Create new emitter device."""
        self.ip = ip
        self.reset()

    def reset(self):
        """Find device on network."""
        self.device = None
        try:
            self.device = broadlink.hello(self.ip)
            self.device.auth()
        except broadlink.exceptions.NetworkTimeoutError:
            pass

    def send_data(self, code: bytes):
        """Send code."""
        if not self.device:
            self.reset()
        self.device.send_data(code)


class RemoteButton():
    """Wrapper class for IR remote button."""

    def __init__(self, name: str, codes: list[str]):
        """Create new button."""
        self.name = name
        self.codes = codes


class Remote():
    """Wrapper class for IR remote."""

    def __init__(self, ip: str, buttons: list[RemoteButton]):
        """Create new button."""
        self.emitter = Emitter(ip)
        self.buttons = buttons

    def press_button(self, index: int):
        """Perform actions."""
        for code in self.buttons[index].codes:
            self.emitter.send_data(base64.b64decode(code))
