import base64

import broadlink


class Emitter:
    def __init__(self, ip: str):
        self.ip = ip
        self.reset()

    def reset(self) -> None:
        self.device = None
        try:
            self.device = broadlink.hello(self.ip)
            self.device.auth()
        except broadlink.exceptions.NetworkTimeoutError:
            pass

    def send_data(self, code: bytes) -> None:
        if not self.device:
            self.reset()
        if self.device:
            self.device.send_data(code)


class RemoteButton:
    def __init__(self, name: str, codes: list[str]):
        self.name = name
        self.codes = codes


class Remote:
    def __init__(self, ip: str, buttons: list[RemoteButton]):
        self.emitter = Emitter(ip)
        self.buttons = buttons

    def press_button(self, index: int) -> None:
        for code in self.buttons[index].codes:
            self.emitter.send_data(base64.b64decode(code))
