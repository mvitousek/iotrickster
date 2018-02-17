To run, navigate to the project's root directory in a terminal and run:

    export FLASK_APP=main.py
    gunicorn main:app --bind 0.0.0.0:8712 -w 4 -k eventlet

or,

    nohup gunicorn main:app --bind 0.0.0.0:8712 -w 4 -k eventlet </dev/null >log.log 2>&1 &