"""Flask web server for home automation."""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, wait

from blinky import Wemo  # installed locally (run.sh)

import broadlink

from flask import Flask, __version__ as flask_version, render_template, request

from ir_library import Librarian  # installed locally (run.sh)

import pkg_resources

# uwsgi callable
application = Flask(__name__)

# belkin brand wemo wifi switches config
SWITCHES = [
    Wemo('192.168.1.81', 1),
    Wemo('192.168.1.84', 1),
    Wemo('192.168.1.83', 1),
    Wemo('192.168.1.85', 1)
]

# broadlink infared emitter config
IR = {
    'buttons': [],
    'librarian': Librarian('/home/pi/ir-tools/ir_library'),
    'device': None
}


# add buttons which each can do 1-N IR actions
def _add_button(name, actions=[]):
    IR['buttons'].append({
        'name': name,
        'actions': json.dumps(actions)
    })


_add_button('power',          [('tv', 'power'), ('sound_bar', 'power')])
_add_button('source',         [('tv', 'source')])
_add_button('vol up',         [('sound_bar', 'vol_up')])
_add_button('vol down',       [('sound_bar', 'vol_down')])
_add_button('1 - chromecast', [('switch', '1')])
_add_button('2 - retropi',    [('switch', '2')])
_add_button('3 - N64',        [('switch', '3')])
_add_button('4 - streamer',   [('switch', '4')])
_add_button('5 - antenna',    [('switch', '5')])
_add_button('mute',           [('sound_bar', 'mute')])


# try to initialize emitter on app start, but don't let failure block startup
def _init_ir(timeout=5):
    devices = broadlink.discover(timeout)
    devices[0].auth()
    return devices[0]


try:
    IR['device'] = _init_ir(10)
except:  # noqa:E722
    pass


def _ir_send(remote, button):
    if not IR['device']:
        IR['device'] = _init_ir()
    code = IR['librarian'].read(
        remote,
        button
    )
    IR['device'].send_data(code)


@application.route('/version')
def version():
    """Return package and python versions as JSON."""
    return {
        'flask': flask_version,
        'broadlink': pkg_resources.get_distribution('broadlink').version,
        'py': sys.version
    }


@application.route('/switches', methods=['GET', 'POST'])
def switches():
    """Wifi switch control.

    GET:return grid of buttons for wifi switches, js reloads page on press
    POST: toggle switch at index
    """  # noqa
    if request.method == 'POST':
        SWITCHES[int(request.values.get('index'))].toggle()
        return ''
    elif request.method == 'GET':

        # structure for representation of switch on page
        def output_obj(status, name, ip=''):
            return {
                'status': status,
                'name': name,
                'ip': ip
            }

        # pull data from one switch, handle errors gracefully
        def fetch_data(switch):
            try:
                name = switch.identify()
            except Exception as e:
                name = str(e)
            try:
                status = switch.status()
            except:  # noqa:722
                status = 'Error'
            return output_obj(status, name, switch.ip)

        # current state of SWITCHES to return
        output = []

        # get switch data in parallel jobs
        executor = ThreadPoolExecutor(max_workers=len(SWITCHES))
        jobs = [executor.submit(fetch_data, switch) for switch in SWITCHES]

        # run jobs and cleanup (timeout won't work with context manager)
        wait(jobs, timeout=2, return_when='ALL_COMPLETED')
        executor.shutdown(wait=False)

        # build output according to job result (preserve order)
        for job in jobs:
            try:
                if job.done():
                    output.append(job.result())
                else:
                    output.append(output_obj('Error', 'JobTimeout'))
            except Exception as e:
                output.append(output_obj('Error', str(e)))

        return render_template('switches.html', switches=output)


@application.route('/goal')
def goal():
    """Return "we just scored" in iframe and turn on goal lights."""
    SWITCHES[0].on()
    return render_template('goal.html', team=request.args.get('team', 'nyr'))


@application.route('/ir_press')
def ir_press():
    """Forward ir packet according to remote and button name."""
    _ir_send(request.values.get('remote'), request.values.get('button'))
    return ''


@application.route('/remote')
def remote():
    """Return grid of buttons which will emit ir packets via js."""
    return render_template('remote.html', options=IR['buttons'])


@application.route('/bedtime')
def bedtime():
    """Perform actions to prepare for bedtime."""
    chromecast_ip = '192.168.1.220'
    result = os.system('ping -c 1 %s > /dev/null 2>&1' % chromecast_ip)
    if result == 0:
        _ir_send('tv', 'power')
        _ir_send('sound_bar', 'power')
    SWITCHES[2].off()
    SWITCHES[1].on()
    return 'Goodnight!'
