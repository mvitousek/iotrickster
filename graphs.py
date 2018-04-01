from datetime import datetime, timedelta

import json
import plotly


def graph_temp(db, mac):
    cur = db.execute('select unixtime, temperature from temp_records where mac="{}" order by id'.format(mac))

    times, temps = [], []
    last_time, last_temp = None, 0

    for time, temp in cur.fetchall():
        if last_time is not None and time - last_time > 7200:
            times.append(None)
            temps.append(last_temp) # If we put 0 here, it will affect plotly's axis scaling
        last_time = time
        last_temp = temp
        times.append(datetime.fromtimestamp(time))
        temps.append(temp * (9 / 5) + 32)

    graph = {
        'data': [ {
            'x': times,
            'y': temps,
            'type': 'scatter',
            'mode': 'lines'
        } ],
        'layout': {
            'title': 'History',
            'yaxis': {
                'autorange': True,
                'ticksuffix': '°F',
                'tickformat': '.1f'
            },
            'xaxis': {
                'type': 'date',
                'tickformatstops':
                [
                    {
                        'dtickrange': [0, 1000 * 60 * 60 * 12],
                        'value': '%-I:%M%p'
                    },
                    {
                        'dtickrange': [1000 * 60 * 60 * 12, 1000 * 60 * 60 * 24 * 28],
                        'value': '%-I:%M%p, %b %-d'
                    },
                    {
                        'dtickrange': [1000 * 60 * 60 * 24 * 28, None],
                        'value': '%b %-d, %Y'
                    }
                ],
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
