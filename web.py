"""Flask web server for home automation."""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait

from config import IR_EMITTER
from config import REMOTES
from config import SWITCHES

from flask import Flask
from flask import Response
from flask import __version__ as flask_version
from flask import render_template
from flask import request

import pkg_resources

# uwsgi callable
application = Flask(__name__)


def _ping(ip, count):
    return os.system(f'ping -c {count} {ip} > /dev/null 2>&1')


@application.route('/')
def hello():
    """Hello World."""
    return 'Hello'


@application.route('/up')
def up():
    """Uptime check endpoint."""
    return Response(str(200), status=200)


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
    remote = request.values.get('remote')
    button = request.values.get('button')
    if remote == 'switch' and button == '3':
        os.system('sudo uhubctl -a cycle -l 1-1 -p 2 > /dev/null 2>&1')
    else:
        IR_EMITTER.send_code(remote, button)
    return ''


@application.route('/remote')
def remote():
    """Return grid of buttons which will emit ir packets via js."""
    remote_name = request.args.get('r', 'main')
    if remote_name not in REMOTES:
        return 'Remote does not exists!'
    output = []
    for button in REMOTES[remote_name].buttons:
        output.append({
            'name': button.name,
            'actions': json.dumps(button.actions)
        })
    return render_template(
        'remote.html', options=output)


@application.route('/bedtime')
def bedtime():
    """Perform actions to prepare for bedtime."""
    chromecast_ip = '192.168.50.220'
    result = _ping(chromecast_ip, 1)
    if result == 0:
        IR_EMITTER.send_code('tv', 'power')
        IR_EMITTER.send_code('sound_bar', 'power')
    SWITCHES[0].off()
    SWITCHES[1].off()
    SWITCHES[2].off()
    SWITCHES[4].on()
    SWITCHES[5].off()
    return 'Goodnight!'


@application.route('/sleeptime')
def sleeptime():
    """Perform actions to prepare for sleeptime."""
    SWITCHES[4].off()
    return 'Goodnight!'
