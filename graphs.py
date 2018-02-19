from datetime import datetime, timedelta

import json
import plotly

def graph_temp(db, mac):
    cur = db.execute('select unixtime, temperature from temp_records where mac="{}" order by id'.format(mac))
    data = cur.fetchall()

    unixtimes, temps = zip(*data)
    times = [datetime.fromtimestamp(t) for t in unixtimes]

    graph = {
        'data': [ {
            'x': times,
            'y': [c * (9 / 5) + 32 for c in temps],
            'type': 'scatter',
            'mode': 'lines'
        } ],
        'layout': {
            'title': 'Temperature',
            'yaxis': {
                'autorange': True,
                'ticksuffix': '°F'
            },
            'xaxis': {
                'type': 'date',
                'rangeselector': {'buttons': [
                    {
                        'count': 1,
                        'label': '1d',
                        'step': 'day',
                        'stepmode': 'backward'
                    },
                    {
                        'count': 3,
                        'label': '3d',
                        'step': 'day',
                        'stepmode': 'backward'
                    },
                    {
                        'count': 7,
                        'label': '1w',
                        'step': 'day',
                        'stepmode': 'backward'
                    },
                    {
                        'count': 1,
                        'label': '1m',
                        'step': 'month',
                        'stepmode': 'backward'
                    },
                    {
                        'count': 1,
                        'label': '1y',
                        'step': 'year',
                        'stepmode': 'backward'
                    }
                ]},
                'range': [times[-1] - timedelta(days=1), times[-1]]
            }
        }
    }
    
    graph_json = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)
    return graph_json
