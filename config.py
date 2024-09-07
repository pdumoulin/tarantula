"""Static configs for web server."""

import traceback

from blinky import Wemo  # installed locally (run.sh)

import broadlink

from ir_library import Librarian  # installed locally (run.sh)


# belkin brand wemo wifi switches config
SWITCHES = [
    (Wemo('192.168.50.100', 1), True),
    (Wemo('192.168.50.196', 1), True),
    (Wemo('192.168.50.190', 1), True),
    (Wemo('192.168.50.199', 1), True),
    (Wemo('192.168.50.178', 1), True),
    (Wemo('192.168.50.242', 1), False),
    (Wemo('192.168.50.200', 1), True)
]


class Emitter():
    """Wrapper class for IR device handling."""

    def __init__(self, index=0, timeout=10):
        self.index = 0
        self.timeout = 10
        self.codes = Librarian('/home/pi/projects/ir-tools/ir_library')
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
            self.init_device()
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
    ]),
    Remote('antenna', [
        RemoteButton(
            'power', [('antenna', 'power')]),
        RemoteButton(
            'ok', [('antenna', 'ok')]),
        RemoteButton(
            'up', [('antenna', 'channel_up')]),
        RemoteButton(
            'down', [('antenna', 'channel_down')]),
        RemoteButton(
            '0', [('antenna', '0')]),
        RemoteButton(
            '1', [('antenna', '1')]),
        RemoteButton(
            '2', [('antenna', '2')]),
        RemoteButton(
            '3', [('antenna', '3')]),
        RemoteButton(
            '4', [('antenna', '4')]),
        RemoteButton(
            '5', [('antenna', '5')]),
        RemoteButton(
            '6', [('antenna', '6')]),
        RemoteButton(
            '7', [('antenna', '7')]),
        RemoteButton(
            '8', [('antenna', '8')]),
        RemoteButton(
            '9', [('antenna', '9')]),
    ]),
    Remote('blu_ray', [
        RemoteButton(
            'power', [('blu_ray', 'power')]),
        RemoteButton(
            'enter', [('blu_ray', 'select')]),
        RemoteButton(
            'up', [('blu_ray', 'up')]),
        RemoteButton(
            'down', [('blu_ray', 'down')]),
        RemoteButton(
            'left', [('blu_ray', 'left')]),
        RemoteButton(
            'right', [('blu_ray', 'right')]),
        RemoteButton(
            'play', [('blu_ray', 'play')]),
        RemoteButton(
            'pause', [('blu_ray', 'pause')]),
        RemoteButton(
            '<<', [('blu_ray', 'rewind')]),
        RemoteButton(
            '>>', [('blu_ray', 'fast_forward')]),
        RemoteButton(
            'menu', [('blu_ray', 'menu')]),
        RemoteButton(
            'stop', [('blu_ray', 'stop')]),
    ])
]
REMOTES = {}
for remote in REMOTES_LIST:
    REMOTES[remote.name] = remote
