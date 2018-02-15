import socketserver, socket
import time
import threading
from retic.typing import *

@fields({'record': List[Tuple[time.struct_time, Any]]})
class Log:
    def __init__(self:'TimedLog'):
        self.record = []

    def log(self:'TimedLog', log_time: time.struct_time, log_data)->None:
        self.record.append((log_time, log_data))

    def last_reading(self:'TimedLog')->Tuple[time.struct_time, Any]:
        return self.record[-1]

    def __len__(self:'TimedLog')->int:
        return len(self.record)

@fields({'mac': str, 'updates': Log, 'temperatures': Log})
class Device:
    def __init__(self:'Device', mac:str):
        self.mac = mac
        self.updates = Log()
        self.temperatures = Log()

    def record_temp(self:'Device', temp:float)->None:
        cur_time = time.gmtime()
        self.temperatures.log(cur_time, temp)

    def update(self:'Device', msg:str)->None:
        cur_time = time.gmtime()
        self.updates.log(cur_time, msg)

    def current_temp(self:'Device')->float:
        _, temp = self.temperatures.last_reading()
        return temp

    def temp_recorded(self:'Device')->bool:
        return len(self.temperatures) > 0


class TempSensorHandler(socketserver.StreamRequestHandler):
    def handle(self:'TempSensorHandler')->None:
        # self.request is the TCP socket connected to the client
        self.data = self.rfile.readline().strip()
        cur_time = time.localtime()
        print("at {}:{:02d}:{:02d}, {} wrote: ".format(cur_time.tm_hour, cur_time.tm_min, cur_time.tm_sec, self.client_address[0]), self.data)
        try:
            mac, command, *args = self.data.split()
        except ValueError:
            print('Bad format')
            return
        device = self.register(mac.decode('utf-8'))
        command = command.decode('utf-8')
        if command == 'register':
            pass
        elif command == 'update':
            device.update(' '.join(arg.decode('utf-8') for arg in args))
        elif command == 'temperature':
            temp, = args
            device.record_temp(float(temp))
        else:
            print('Command {} unrecognized'.format(command))

    def register(self:'TempSensorHandler', mac:str)->Device:
        if mac not in self.server.devices:
            device = Device(mac)
            self.server.devices[mac] = device
        else:
            device = self.server.devices[mac]
        return device

        
            
        

def get_ip()->str:    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('255.255.255.0', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@fields({'devices':Dict[str, Device]})
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def __init__(self:'ThreadedTCPServer', devices:Dict[str, Device], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.devices = devices

def start_server(host, port):
    devices = {}
    ThreadedTCPServer.allow_reuse_address = True
    server = ThreadedTCPServer(devices, (host, port), TempSensorHandler)
    server_thread = threading.Thread(target=server.serve_forever)

    server_thread.daemon = True
    server_thread.start()
    return devices

if __name__ == "__main__":
    HOST, PORT = '0.0.0.0', 8712

    start_server(HOST, PORT)
    while True: pass
