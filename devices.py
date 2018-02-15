import time

try:
    from retic.typing import *
except ImportError:
    from retic_dummies import *

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

@fields({'mac': str, 'updates': Log, 'temperatures': Log, 'alias':str})
class Device:
    def __init__(self:'Device', mac:str):
        self.mac = mac
        self.alias = None
        self.updates = Log()
        self.temperatures = Log()

    def record_temp(self:'Device', temp:float)->None:
        cur_time = time.gmtime()
        self.temperatures.log(cur_time, temp)

    def update(self:'Device', msg:str)->None:
        cur_time = time.gmtime()
        self.updates.log(cur_time, msg)

    def last_temp(self:'Device')->Tuple[time.struct_time, float]:
        return self.temperatures.last_reading()

    def temp_recorded(self:'Device')->bool:
        return len(self.temperatures) > 0

    def get_alias(self:'Device')->str:
        if self.alias is not None:
            return self.alias
        else:
            return self.mac

        
            
        
