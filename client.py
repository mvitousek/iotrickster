import time
import threading
import requests


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
        data = requests.post('{}/socketmessage.php'.format(self.url), data={'messageType': 'getTemperatures'})
        data = data.json()
        
        beertemp = data['BeerTemp']
        beertemp = (beertemp - 32) * (5 / 9)
        requests.post('{}/signal/temp'.format(iotrickster), data={'temp':beertemp, 'mac':'{}$beer'.format(self.id)})
        
        fridgetemp = data['FridgeTemp']
        fridgetemp = (fridgetemp - 32) * (5 / 9)
        requests.post('{}/signal/temp'.format(iotrickster), data={'temp':fridgetemp, 'mac':'{}$fridge'.format(self.id)})
        
        time.sleep(60)


        
iotrickster = 'http://localhost:8712'
dev = BrewPiClientDevice('brewpi', 'http://68.54.119.232:8000')
dev.start()
