
from blinky import wemo
from flask import Flask, request, render_template
application = Flask(__name__)

SWITCHES = [
    wemo('192.168.1.81'),
    wemo('192.168.1.83'),
    wemo('192.168.1.85')
]

@application.route("/switches", methods=['GET', 'POST'])
def switches():
    if request.method == 'POST':
        SWITCHES[int(request.values.get('index'))].toggle()
        return ''
    elif request.method == 'GET':
        output = []
        for switch in SWITCHES:
            output.append({
                'status' : switch.status(),
                'name'   : switch.name()
            })
    return render_template('switches.html', switches=output)

@application.route("/goal")
def goal():
    SWITCHES[0].toggle()
    return render_template('goal.html', 
        team=request.args.get('team', 'nyr'))

