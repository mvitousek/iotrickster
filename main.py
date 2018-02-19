import os.path
import time, calendar
import sqlite3 as sql

import graphs

from flask import *

try:
    from retic.typing import *
except ImportError:
    # If you don't have Reticulated Python installed
    from retic_dummies import *

# Type aliases:
DB = sql.Connection
Row = sql.Row


HOST, PORT = 'localhost', 8712
DB_INTERVAL_SECONDS = 3600

app = Flask('iotrickster')
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    DATABASE=os.path.join(app.root_path, 'database', 'iotrickster.db'),
    LATEST={}
))

app.config.from_envvar('IOTRICKSTER_SETTINGS', silent=True)

@app.route('/')
def index():
    db = get_db()

    # Get all devices and their names
    cur = db.execute('select mac, devalias from aliases order by lower(devalias)')
    devices = cur.fetchall()
    
    data = []
    for mac, alias in devices:
        unixtime, temp = get_last(db, mac)
        time, date = format_gmt_for_local(unixtime)
        data.append((mac, alias, time, date, temp))
        
    return render_template('index.html', data=data, tempformat=c_to_f)

def get_last(db:DB, mac:str)->Tuple[int, float]:
    latest = get_latest()
    if mac in latest:
        unixtime, temp, _ = latest[mac]
    else:
        cur = db.execute('select max(id), unixtime, temperature from temp_records where mac="{}"'.format(mac))
        _, unixtime, temp = cur.fetchone()
    return unixtime, temp
    

def get_logs(db:DB, mac:str, count:int, offset:int=0)->List[sql.Row]:
    cur = db.execute('select unixtime, temperature from temp_records where mac="{}" order by id desc limit {} offset {}'.format(mac, count, offset))
    return cur.fetchall()

def get_alias(db:DB, mac:str)->str:
    cur = db.execute('select devalias from aliases where mac="{}"'.format(mac))
    alias, = cur.fetchone()
    return alias

@app.route('/details/<mac>')
def details(mac:str):
    db = get_db()

    alias = get_alias(db, mac)
    data = get_logs(db, mac, 12)
    assert len(data) <= 12

    graph = graphs.graph_temp(db, mac)

    unixtime, temp = get_last(db, mac)
    
    return render_template('details.html', last_time=unixtime, last_temp=temp, graph=graph, mac=mac, alias=alias, data=data, tdformat=format_gmt_for_local, tempformat=c_to_f)

@app.route('/details/<mac>/<count>/<offset>')
def history(mac:str, count:int, offset:int):
    db = get_db()

    alias = get_alias(db, mac)
    data = get_logs(db, mac, count, offset)
    cur = db.execute('select count(*) from temp_records where mac="{}"'.format(mac, count, offset))
    total, = cur.fetchone()
    
    return render_template('history.html', mac=mac, alias=alias, offset=offset, count=count, data=data, total=total, tdformat=format_gmt_for_local, tempformat=c_to_f)

@app.route('/details/<mac>/set_alias', methods=['POST'])
def set_alias(mac:str):
    alias = request.form['new_alias']
    
    db = get_db()
    db.execute('update aliases set devalias="{}" where mac="{}"'.format(alias, mac))
    db.commit()
    
    return redirect(url_for('details', mac=mac))


# Sensors POST to this address, shouldn't be usable from browser
@app.route('/signal/temp', methods=['POST'])
def signal_temp():
    # Request has mac address 'mac' and temperature 'temp' fields
    mac = request.form['mac']
    temp = float(request.form['temp'])
    unixtime = time.time()
    
    db = get_db()
    latest = get_latest()
    
    if mac not in latest:
        cur = db.execute('select exists (select 1 from aliases where mac="{}" limit 1)'.format(mac))
        exists = cur.fetchone()[0]
        recents = []
        if not exists:
            db.execute('insert into aliases (mac, devalias) values ("{}", "{}")'.format(mac, mac))
    else:
        _, _, recents = latest[mac]
        exists = True

    # If this is the first time we've seen this thing then we definitely insert into DB, otherwise we have to check
    if mac in latest or exists:
        
        # Don't use get_latest here, because we want to know if it's time to make another permanent record
        cur = db.execute('select max(id), unixtime, temperature from temp_records where mac="{}"'.format(mac))
        _, last_db_time, last_db_temp = cur.fetchone()

        need_to_insert = unixtime - last_db_time > DB_INTERVAL_SECONDS
        print(need_to_insert)
    else:
        need_to_insert = True

    recents.append(temp)
    if need_to_insert:
        # Insert a record into the temperature log.
        avg_temp = sum(recents) / len(recents)
        db.execute('insert into temp_records (mac, unixtime, temperature) values (\"{}\", {}, {})'.format(mac, unixtime, avg_temp))
        recents = []
        
    latest[mac] = unixtime, temp, recents

    db.commit()

    # redirect is unneccessary, dunno what else to put here
    return redirect(url_for('index'))

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def c_to_f(c:float)->str:
    return '{:.1f}°F'.format(c * (9 / 5) + 32)

def unix_to_local(epoch:int)->time.struct_time:
    return time.localtime(epoch)

def format_gmt_for_local(epoch:int)->Tuple[str,str]:
    t = unix_to_local(epoch)
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

def get_db()->DB:
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def get_latest()->Dict[str, Tuple[int, float]]:
    if not hasattr(g, 'latest_dict'):
        g.latest_dict = app.config['LATEST']
    return g.latest_dict

def connect_db()->DB:
    rv = sql.connect(app.config['DATABASE'])
    rv.row_factory = sql.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource(os.path.join('database', 'schema.sql'), mode='r') as f:
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
