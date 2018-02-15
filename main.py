import devices
import time, calendar
from flask import *
app = Flask('iottrickster')

@app.route("/")
def index():    
    return render_template('index.html', devices=get_devices(), c_to_f=c_to_f, gmt_to_local=gmt_to_local)

@app.route('/details/<mac>')
def details(mac):
    return render_template('details.html', mac=mac)

@app.route('/signal/temp', methods=['POST'])
def signal_temp():
    mac = request.form['mac']
    temp = request.form['temp']
    devs = get_devices()
    if mac not in devs:
        devs[mac] = devices.Device(mac)
    devs[mac].record_temp(float(temp))
    return redirect(url_for('index'))

def c_to_f(c:float)->float:
    return c * (9 / 5) + 32

def gmt_to_local(t:time.struct_time)->time.struct_time:
    tm = time.localtime(calendar.timegm(t))
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
    
#    devices = temp_server.start_server(HOST, PORT)
    app.config.update(dict(
        DEBUG=True,
        DEVICES={},
        SECRET_KEY=b'MYSECRETKEY',
        USERNAME='admin',
        PASSWORD='default'
    ))
    app.config.from_envvar('IOTRICKSTER_SETTINGS', silent=True)
    app.run(host=HOST, port=PORT, debug=True)
