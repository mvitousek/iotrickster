import temp_server
import time, calendar
from flask import *
app = Flask('iottrickster')

@app.route("/")
def index():    
    return render_template('index.html', devices=get_devices(), c_to_f=c_to_f)

@app.route('/signal/temp', methods=['POST'])
def signal_temp():
    mac = request.form['mac']
    temp = request.form['temp']
    devices = get_devices()
    if mac not in devices:
        devices[mac] = temp_server.Device(mac)
    devices[mac].record_temp(float(temp))
    return redirect(url_for('index'))

def c_to_f(c:float)->float:
    return c * (9 / 5) + 32

def gmt_to_local(t:time.struct_time)->time.struct_time:
    return time.localtime(calendar.timegm(t))


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
