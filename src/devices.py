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
