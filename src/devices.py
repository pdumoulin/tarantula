import base64

import broadlink


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
        self.device.auth()

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
