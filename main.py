import devices
import time, calendar
import sqlite3 as sql
try:
    from retic.typing import *
except ImportError:
    from retic_dummies import *

from flask import *

app = Flask('iotrickster')

@app.route("/")
def index():    
    return render_template('index.html', devices=get_devices(), c_to_f=c_to_f, timeformat=format_gmt_for_local)

@app.route('/details/<mac>')
def details(mac):
    dev = get_devices()[mac]
    return render_template('details.html', dev=dev, c_to_f=c_to_f, timeformat=format_gmt_for_local)

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
    return time.localtime(calendar.timegm(t))

def format_gmt_for_local(t:time.struct_time)->Tuple[str,str]:
    t = gmt_to_local(t)
    ampm = 'am'
    hour = t.tm_hour
    if hour == 0:
        hour = 12
    elif hour >= 12:
        ampm = 'pm'
        if hour > 12:
            hour -= 12
    return '{}:{:02d}:{:02d}{}'.format(hour, t.tm_min, t.tm_sec, ampm),\
           '{}/{}/{}'.format(t.tm_year, t.tm_mon, t.tm_mday)

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
