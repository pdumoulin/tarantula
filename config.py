"""Static configs for web server."""

import traceback

from blinky import Wemo  # installed locally (run.sh)

import broadlink

from ir_library import Librarian  # installed locally (run.sh)


# belkin brand wemo wifi switches config
SWITCHES = [
    Wemo('192.168.1.81', 1),
    Wemo('192.168.1.84', 1),
    Wemo('192.168.1.83', 1),
    Wemo('192.168.1.85', 1)
]


class Emitter():
    """Wrapper class for IR device handling."""

    def __init__(self, index=0, timeout=10):
        self.index = 0
        self.timeout = 10
        self.codes = Librarian('/home/pi/ir-tools/ir_library')
        self.device = None
        self.init_device()

    def init_device(self):
        try:
            devices = broadlink.discover(self.timeout)
            devices[self.index].auth()
            self.device = devices[self.index]
        except:  # noqa:E722
            print(traceback.format_exc())

    def send_code(self, remote, button):
        if not self.device:
            self.device = self.init_device()
        code = self.codes.read(
            remote,
            button
        )
        self.device.send_data(code)


IR_EMITTER = Emitter()

# TODO - think about moving Emitter to Remote object
# TODO - move these classes to model & add docstrings

class Remote():

    def __init__(self, name, buttons):
        self.name = name
        self.buttons = buttons


class RemoteButton():

    def __init__(self, name, actions):
        self.name = name
        self.actions = actions


REMOTES_LIST = [
    Remote('main', [
        RemoteButton(
            'power', [('tv', 'power'), ('sound_bar', 'power')]),
        RemoteButton(
            'source', [('tv', 'source')]),
        RemoteButton(
            'vol up', [('sound_bar', 'vol_up')]),
        RemoteButton(
            'vol down', [('sound_bar', 'vol_down')]),
        RemoteButton(
            '1 - chromecast', [('switch', '1')]),
        RemoteButton(
            '2 - retropi', [('switch', '2')]),
        RemoteButton(
            '3 - N64', [('switch', '3')]),
        RemoteButton(
            '4 - streamer', [('switch', '4')]),
        RemoteButton(
            '5 - antenna', [('switch', '5')]),
        RemoteButton(
            'mute', [('sound_bar', 'mute')])
    ])
]
REMOTES = {}
for remote in REMOTES_LIST:
    REMOTES[remote.name] = remote
