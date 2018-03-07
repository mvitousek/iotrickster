import time
import threading
import sys
import requests

import argparse

try:
    from retic.typing import *
except ImportError:
    # If you don't have Reticulated Python installed
    from retic_dummies import *


@fields({'id':str, 'url':str})
class BrewPiClientDevice(threading.Thread):
    def __init__(self, id:str, url:str):
        super().__init__()
        self.id = id
        if url.endswith('/'):
            raise Exception('URL should not include a terminating slash')
        self.url = url
    def run(self):
        while True:
            data = requests.post('{}/socketmessage.php'.format(self.url), data={'messageType': 'getTemperatures'})
            data = data.json()

            beertemp = data['BeerTemp']
            beertemp = (beertemp - 32) * (5 / 9)
            requests.post('{}/signal/temp'.format(iotrickster), data={'temp':beertemp, 'mac':'{}beer'.format(self.id)})

            fridgetemp = data['FridgeTemp']
            fridgetemp = (fridgetemp - 32) * (5 / 9)
            requests.post('{}/signal/temp'.format(iotrickster), data={'temp':fridgetemp, 'mac':'{}fridge'.format(self.id)})

            time.sleep(60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Proxy between existing connected device and IoTrickster')
    parser.add_argument('host', help='IoTrickster host and port')
    parser.add_argument('--brewpi', help='BrewPi host and port', default=None)
    
    args = parser.parse_args(sys.argv[1:])
    iotrickster = args.host

    clients = []

    if args.brewpi:
        client = BrewPiClientDevice('brewpi', args.brewpi)
        client.start()
        clients.append(client)

    for client in clients:
        client.join()

    
        
