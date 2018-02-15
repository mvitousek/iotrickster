import socket
import sys
import time
import requests

HOST, PORT = "192.168.1.116", 8712

while(True):
    try:
        response = requests.post("http://192.168.1.116:8712/signal/temp", data={'mac': 'laptop', 'temp': 25.0})
        print(response)
    except requests.exceptions.ConnectionError:
        print('Connection refused')
    time.sleep(5)
    
