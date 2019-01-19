
from multiprocessing.pool import ThreadPool
from blinky import wemo
from ir_library import Librarian
from ir_devices import DeviceList
from flask import Flask, request, render_template
application = Flask(__name__)

SWITCHES = [
    wemo('192.168.1.81', 1),
    wemo('192.168.1.84', 1),
    wemo('192.168.1.83', 1),
    # wemo('192.168.1.82', 1),
    wemo('192.168.1.85', 1)
]

IR_BUTTONS = [
    {'name' : 'power', 'remote' : 'tv', 'button' : 'power'},
    {'name' : 'source', 'remote' : 'tv', 'button' : 'source'},
    {'name' : 'enter', 'remote' : 'tv', 'button' : 'enter'},
    {'name' : 'exit', 'remote' : 'tv', 'button' : 'exit'},
    {'name' : '1 - chromecast', 'remote' : 'switch', 'button' : '1'},
    {'name' : '2 - retropie', 'remote' : 'switch', 'button' : '2'},
    {'name' : '3 - N64', 'remote' : 'switch', 'button' : '3'},
    {'name' : '4 - computer', 'remote' : 'switch', 'button' : '4'},
    {'name' : '5 - antenna', 'remote' : 'switch', 'button' : '5'},
    {'name' : 'info', 'remote' : 'tv', 'button' : 'info'}
]

IR_LIBRARIAN = Librarian('/home/pi/ir-tools/ir_library/')
IR_DEVICE = DeviceList().get('default')

@application.route("/on")
def on():
    SWITCHES[int(request.values.get('index'))].on()
    return ''

@application.route("/off")
def off():
    SWITCHES[int(request.values.get('index'))].off()
    return ''

@application.route("/toggle")
def toggle():
    SWITCHES[int(request.values.get('index'))].toggle()
    return ''

@application.route("/switches", methods=['GET', 'POST'])
def switches():
    if request.method == 'POST':
        SWITCHES[int(request.values.get('index'))].toggle()
        return ''
    elif request.method == 'GET':
        def output_obj(status, name, ip):
            return {
                'status' : status,
                'name'   : name,
                'ip'     : ip
            }
        def fetch_data(switch):
            status = 1 if switch.status() in switch.ON_STATES else 0
            return output_obj(
                status,
                switch.identify(),
                switch.ip
            )

        pool = ThreadPool(processes=3)
        workers = [pool.apply_async(fetch_data, (switch,)) for switch in SWITCHES]
        # output = [worker.get(timeout=5) for worker in workers]
        output = []
        for worker in workers:
            try:
                output.append(worker.get(timeout=5))
            except Exception as e:
                output.append(output_obj(2, str(e), ''))
        pool.close()
    return render_template('switches.html', switches=output)

@application.route("/goal")
def goal():
    SWITCHES[0].toggle()
    return render_template('goal.html', team=request.args.get('team', 'nyr'))

@application.route("/ir_press")
def ir_press():
    remote_input = request.values.get('remote')
    button_input = request.values.get('button')
    code = IR_LIBRARIAN.read(remote_input, button_input)
    IR_DEVICE.send_data(code)
    return ''

@application.route("/remote")
def remote():
    return render_template('remote.html', options=IR_BUTTONS)
