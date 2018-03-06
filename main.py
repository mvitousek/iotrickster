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
    DATABASE=os.path.join(app.root_path, 'database', 'iotrickster.db')
))

app.config.from_envvar('IOTRICKSTER_SETTINGS', silent=True)

@app.context_processor
def utility_processor():
    return dict(time=time.time)

@app.route('/')
def index():
    db = get_db()

    # Get all devices and their names
    cur = db.execute('select mac, devalias, intermittent from aliases order by lower(devalias)')
    devices = cur.fetchall()
    
    data = []
    for mac, alias, intermittent in devices:
        unixtime, temp = get_last(db, mac)
        time, date = format_gmt_for_local(unixtime)
        data.append((mac, alias, bool(int(intermittent)), unixtime, time, date, temp))
        
    return render_template('index.html', data=data, tempformat=c_to_f)

def get_last(db:DB, mac:str)->Tuple[int, float]:
    cur = db.execute('select max(id), unixtime, temperature from temp_short_term_records where mac="{}"'.format(mac))
    _, unixtime, temp = cur.fetchone()
    return unixtime, temp
    

def get_logs(db:DB, mac:str, count:int, offset:int=0)->List[sql.Row]:
    cur = db.execute('select unixtime, temperature from temp_records where mac="{}" order by id desc limit {} offset {}'.format(mac, count, offset))
    return cur.fetchall()

def get_alias(db:DB, mac:str)->str:
    cur = db.execute('select devalias from aliases where mac="{}"'.format(mac))
    alias, = cur.fetchone()
    return alias

@app.route('/<mac>')
def details(mac:str):
    db = get_db()

    cur = db.execute('select devalias, intermittent from aliases where mac="{}"'.format(mac))
    alias, intermittent = cur.fetchone()

    unixtime, temp = get_last(db, mac)
    data = get_logs(db, mac, 12)
    assert len(data) <= 12

    graph = graphs.graph_temp(db, mac)

    
    return render_template('details.html', last_time=unixtime, last_temp=temp, graph=graph, mac=mac, 
                           alias=alias, intermittent=bool(int(intermittent)), data=data, 
                           tdformat=format_gmt_for_local, tempformat=c_to_f)

@app.route('/<mac>/raw')
def raw(mac:str):
    db = get_db()
    unixtime, temp = get_last(db, mac)
    
    return '{}\n{}\n'.format(unixtime, temp)

@app.route('/<mac>/<count>-<offset>')
def history(mac:str, count:int, offset:int):
    db = get_db()

    alias = get_alias(db, mac)
    data = get_logs(db, mac, count, offset)
    cur = db.execute('select count(*) from temp_records where mac="{}"'.format(mac, count, offset))
    total, = cur.fetchone()
    
    return render_template('history.html', mac=mac, alias=alias, offset=offset, count=count, data=data, total=total, tdformat=format_gmt_for_local, tempformat=c_to_f)

@app.route('/<mac>/set_alias', methods=['POST'])
def set_alias(mac:str):
    alias = request.form['newalias']
    
    db = get_db()
    db.execute('update aliases set devalias="{}" where mac="{}"'.format(alias, mac))
    db.commit()
    
    return redirect(url_for('details', mac=mac))

@app.route('/<mac>/delete', methods=['POST'])
def delete(mac:str):
    db = get_db()
    db.execute('delete from aliases where mac="{}"'.format(mac))
    db.execute('delete from temp_records where mac="{}"'.format(mac))
    db.execute('delete from temp_short_term_records where mac="{}"'.format(mac))
    db.commit()
    
    return redirect(url_for('index'))

@app.route('/<mac>/intermittent', methods=['POST'])
def intermittent(mac:str):
    intermittent = request.form['intermittent']


    db = get_db()
    db.execute('update aliases set intermittent={} where mac="{}"'.format(intermittent, mac))
    db.commit()
    
    return redirect(url_for('details', mac=mac))


# Sensors POST to this address, shouldn't be usable from browser
@app.route('/signal/temp', methods=['POST'])
def signal_temp():
    # Request has mac address 'mac' and temperature 'temp' fields
    mac = request.form['mac']
    temp = float(request.form['temp'])
    
    if temp == 85:
        return redirect(url_for('index'))

    unixtime = time.time()
    
    db = get_db()
    
    cur = db.execute('select exists (select 1 from aliases where mac="{}" limit 1)'.format(mac))
    exists, = cur.fetchone()
    if not exists:
        db.execute('insert into aliases (mac, devalias, intermittent) values ("{}", "{}", 0)'.format(mac, mac))
        db.execute('insert into temp_records (mac, unixtime, temperature) values (\"{}\", {}, {})'.format(mac, unixtime, temp))
    else:
        cur = db.execute('select unixtime, temperature from temp_short_term_records where mac="{}" order by id'.format(mac))
        top_time, _ = cur.fetchone()
        if unixtime - top_time > DB_INTERVAL_SECONDS:
            # Intentionally ignore the first element, which was already recorded
            rows = cur.fetchall()
            if len(rows) > 0:
                _, temps = zip(*rows)
                temps = list(temps)
                avg_temp = (sum(temps) + temp) / (len(temps) + 1)
            else:
                avg_temp = temp
            db.execute('insert into temp_records (mac, unixtime, temperature) values (\"{}\", {}, {})'.format(mac, unixtime, avg_temp))
            db.execute('delete from temp_short_term_records where mac="{}"'.format(mac))
    db.execute('insert into temp_short_term_records (mac, unixtime, temperature) values (\"{}\", {}, {})'.format(mac, unixtime, temp))
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
    daytime = time.strftime('%-I:%M%p', t)
    yeartime = time.strftime('%a, %b %-d %Y', t)
    return daytime, yeartime

def get_db()->DB:
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

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
