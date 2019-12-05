
import sys
import flask
import broadlink
import pkg_resources

from concurrent.futures import ThreadPoolExecutor, wait
from flask import Flask, request, render_template

# sources installed locally (see run.sh)
from ir_library import Librarian
from blinky import Wemo

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
    'buttons' : [
        {'name' : 'power', 'remote' : 'tv', 'button' : 'power'},
        {'name' : 'source', 'remote' : 'tv', 'button' : 'source'},
        {'name' : 'vol up', 'remote' : 'sound_bar', 'button' : 'vol_up'},
        {'name' : 'vol down', 'remote' : 'sound_bar', 'button' : 'vol_down'},
        {'name' : '1 - chromecast', 'remote' : 'switch', 'button' : '1'},
        {'name' : '2 - retropie', 'remote' : 'switch', 'button' : '2'},
        {'name' : '3 - N64', 'remote' : 'switch', 'button' : '3'},
        {'name' : '4 - computer', 'remote' : 'switch', 'button' : '4'},
        {'name' : '5 - antenna', 'remote' : 'switch', 'button' : '5'},
        {'name' : 'mute', 'remote' : 'sound_bar', 'button' : 'mute'}
    ],
    'librarian' : Librarian('/home/pi/ir-tools/ir_library'),
    'device'    : None
}

# try to initialize emitter on app start, but don't let failure block startup
def _init_ir(timeout=5):
    devices = broadlink.discover(timeout)
    devices[0].auth()
    return devices[0]
try:
    if not IR['device']:
        IR['device'] = _init_ir(10)
except:
    pass


'''
    return package and python versions as JSON
'''
@application.route('/version')
def version():
    return {
        'flask'     : flask.__version__,
        'broadlink' : pkg_resources.get_distribution('broadlink').version,
        'py'        : sys.version
    }

'''
    GET  - return grid of buttons for wifi switches, js reloads page on press
    POST - toggle switch at index in array
'''
@application.route('/switches', methods=['GET', 'POST'])
def switches():
    if request.method == 'POST':
        SWITCHES[int(request.values.get('index'))].toggle()
        return ''
    elif request.method == 'GET':

        # structure for representation of switch on page
        def output_obj(status, name, ip=''):
            return {
                'status' : status,
                'name'   : name,
                'ip'     : ip
            }

        # pull data from one switch, handle errors gracefully
        def fetch_data(switch):
            try:
                name = switch.identify()
            except Exception as e:
                name = str(e)
            try:
                status = switch.status()
            except:
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

'''
    return "we just scored" in iframe and turn on goal lights
'''
@application.route('/goal')
def goal():
    SWITCHES[0].on()
    return render_template('goal.html', team=request.args.get('team', 'nyr'))

'''
    forward ir packet according to remote and button name
'''
@application.route('/ir_press')
def ir_press():
    if not IR['device']:
        IR['device'] = _init_ir()
    code = IR['librarian'].read(
        request.values.get('remote'),
        request.values.get('button')
    )
    IR['device'].send_data(code)
    return ''

'''
    return grid of buttons which will emit ir packets via ja
'''
@application.route('/remote')
def remote():
    return render_template('remote.html', options=IR['buttons'])
