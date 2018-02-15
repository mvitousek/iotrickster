import sys
import time
import requests
import argparse

parser = argparse.ArgumentParser(description='Test the IoTrickster server with bogus data')
parser.add_argument('host', help='Host to use (excluding "http://" or the port', nargs=1)

args = parser.parse_args(sys.argv[1:])
PORT = 8712

while(True):
    try:
        response = requests.post("http://{}:8712/signal/temp".format(args.host), data={'mac': 'test_client', 'temp': 25.0})
        print(response)
    except requests.exceptions.ConnectionError:
        print('Connection refused')
    time.sleep(5)
    
