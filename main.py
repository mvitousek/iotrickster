import devices
import time, calendar
from flask import *

app = Flask('iotrickster')

@app.route("/")
def index():    
    return render_template('index.html', devices=get_devices(), c_to_f=c_to_f, gmt_to_local=gmt_to_local)

@app.route('/details/<mac>')
def details(mac):
    dev = get_devices()[mac]
    return render_template('details.html', dev=dev, c_to_f=c_to_f, gmt_to_local=gmt_to_local)

@app.route('/details/<mac>/set_alias', methods=['POST'])
def set_alias(mac):
    alias = request.form['new_alias']
    dev = get_devices()[mac]
    dev.alias = alias
    return redirect(url_for('details', mac=mac))


# Sensors POST to this address, shouldn't be usable from browser
@app.route('/signal/temp', methods=['POST'])
def signal_temp():
    # Request has mac address 'mac' and temperature 'temp' fields
    mac = request.form['mac']
    temp = request.form['temp']
    devs = get_devices()
    if mac not in devs:
        devs[mac] = devices.Device(mac)
    devs[mac].record_temp(float(temp))
    # redirect is unneccessary, dunno what else to put here
    return redirect(url_for('index'))

def c_to_f(c:float)->float:
    return c * (9 / 5) + 32

def gmt_to_local(t:time.struct_time)->time.struct_time:
    tm = time.localtime(calendar.timegm(t))
    # Also display time in conventional US format with am/pm
    apm = 'am'
    if tm.tm_hour == 0:
        tm.tm_hour = 12
    elif tm.tm_hour >= 12:
        apm = 'pm'
        if tm.tm_hour > 12:
            tm.tm_hour -= 12
    return tm, apm
            

def get_devices():
    return app.config['DEVICES']

if __name__ == "__main__":
    HOST, PORT = '0.0.0.0', 8712
    
    app.config.update(dict(
        DEBUG=True,
        DEVICES={},
    ))
    app.config.from_envvar('IOTRICKSTER_SETTINGS', silent=True)
    app.run(host=HOST, port=PORT, debug=True)
