"""Flask web server for home automation."""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, wait

from config import IR_EMITTER, REMOTES, SWITCHES

from flask import Flask, __version__ as flask_version, render_template, request

import pkg_resources

# uwsgi callable
application = Flask(__name__)


@application.route('/')
def hello():
    """Hello World."""
    return 'Hello'


@application.route('/up')
def up():
    """Uptime check endpoint."""
    return 'OK'


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
    IR_EMITTER.send_code(
        request.values.get('remote'), request.values.get('button'))
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
    chromecast_ip = '192.168.1.220'
    result = os.system('ping -c 1 %s > /dev/null 2>&1' % chromecast_ip)
    if result == 0:
        IR_EMITTER.send_code('tv', 'power')
        IR_EMITTER.send_code('sound_bar', 'power')
    SWITCHES[0].off()
    SWITCHES[1].off()
    SWITCHES[2].on()
    return 'Goodnight!'


@application.route('/sleeptime')
def sleeptime():
    """Perform actions to prepare for sleeptime."""
    SWITCHES[2].off()
    return 'Goodnight!'
