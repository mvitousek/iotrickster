import devices
import os.path
import time, calendar
import sqlite3 as sql
try:
    from retic.typing import *
except ImportError:
    from retic_dummies import *

    
HOST, PORT = '0.0.0.0', 8712

from flask import *

app = Flask('iotrickster')
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    DATABASE=os.path.join(app.root_path, 'iotrickster.db'),
    DEVICES={}
))
app.config.from_envvar('IOTRICKSTER_SETTINGS', silent=True)

@app.route("/")
def index():
    db = get_db()
    cur = db.execute('select mac, devalias from aliases order by mac desc')
    entries = cur.fetchall()
    print(entries)
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

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

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

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def connect_db():
    rv = sql.connect(app.config['DATABASE'])
    rv.row_factory = sql.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

if __name__ == "__main__":
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(host=HOST, port=PORT, debug=True)
