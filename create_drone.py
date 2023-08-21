# from drone_sensor import Sensor
import datetime as dt
from drone_sensor_pre import Sensor
import threading
import time
import random
import get_time
import ast
import uuid
from format_p import *

class create_drone:
    #### ! This function was written by Amit Amola & Stephen Rowe
    def __init__(self, location, this_sensor_tasks, this_interface, ndn):
        """list of all sensors a drone can have
        ['temperature', 'humidity', 'pressure', 'wind_speed', 'cloudiness', 'visibility', 'dew_point']
        list of all actuations a drone can perform
        ['calcium_cl2', 'calcium_no3', 'anti_frost', 'anti_dew'] or None"""
        
        self.this_interface = this_interface # "ip:port" of this device
        self.ndn = ndn
        self.location = location
        self.ndn.location = location
        
        self.all_sensor_tasks = set(['temperature', 'humidity', 'pressure',
                              'wind_speed', 'cloudiness', 'visibility', 
                              'dew_point'])
        
        self.this_sensor_tasks = set(ast.literal_eval(this_sensor_tasks))
        
        self.this_sensor_vals = dict()

        self.sensor_value_assign = Sensor()
        self.assign_vals()

        self.this_device_paths = self.__generate_starter_fib() # this is just for the FIB-related code in node.py, has no relevance to any other aspect of this class
        self.ndn.forwarding_information_base = self.this_device_paths  
        
        threading.Thread(target=self.__actuate_loop).start()          

    def set_location(self, new_location):
        self.location = new_location
        self.ndn.location = self.location
    
    #### ! This function was written by Stephen Rowe
    def __actuate_loop(self):
        #Create a thread to initiate actuation after random time interval between 3 to 30 seconds.
        while True:
            time.sleep(random.randint(3,10)) 
            self.assign_vals()
            self.actuate()
    
    #### ! This function was written by Amit Amola
    def assign_vals(self):
        cur_time = str(get_time.get_time())
        for val in self.this_sensor_tasks:
            
            get_val = eval(f"self.sensor_value_assign.get_{val}('{self.location}', '{cur_time}')")
            key = f"/{self.location}/{val}/{cur_time}"

            self.this_sensor_vals[key] = get_val

        # Updating content store with initial values
        self.ndn.content_store.update(self.this_sensor_vals)

    #### ! This function was written by Amit Amola
    def initiate_actuation(self,cur_time):
        """
        The function initiates actuation if the actuation task is not None
        """
        leftover = self.all_sensor_tasks - self.this_sensor_tasks
                
        interest_packets_to_send = set()
        
        # nonce = uuid.uuid4().hex
        
        for val in leftover:
            name = f"/{self.location}/{val}/{cur_time}"
            if name not in self.ndn.content_store:
                interest_packets_to_send.add(f"Interest|{name}")

        for interest in interest_packets_to_send:
            try: 
                self.ndn.fib(interest)
            except Exception as e:
                printv(e)

    #### ! This function was written by Amit Amola
    def actuate(self):
        cur_time = str(get_time.get_time())
        self.initiate_actuation(cur_time)
        try:
            # Perform actuation
            if float(self.ndn.content_store[f"/{self.location}/visibility/{cur_time}"]) > 53.0:
                printv("No need to actuate")
            elif float(self.ndn.content_store[f"/{self.location}/visibility/{cur_time}"]) <= 53.0 \
                    and float(self.ndn.content_store[f"/{self.location}/pressure/{cur_time}"]) <= 944.5:
                printv('Signs of heavy_rain, spreading CaCl2.')
            elif float(self.ndn.content_store[f"/{self.location}/visibility/{cur_time}"]) <= 53.0 \
                    and float(self.ndn.content_store[f"/{self.location}/pressure/{cur_time}"]) > 944.5\
                    and float(self.ndn.content_store[f"/{self.location}/wind_speed/{cur_time}"]) > 5.0:
                printv('Possibility of small drizzle, spreading Ca(NO3)2.')
            elif float(self.ndn.content_store[f"/{self.location}/visibility/{cur_time}"]) <= 53.0 \
                    and float(self.ndn.content_store[f"/{self.location}/pressure/{cur_time}"]) > 944.5\
                    and float(self.ndn.content_store[f"/{self.location}/wind_speed/{cur_time}"]) <= 5.0\
                    and float(self.ndn.content_store[f"/{self.location}/temperature/{cur_time}"]) > -0.5:
                printv('Temperature is at dew_point, spreading Anti_dew_spray.')
            elif float(self.ndn.content_store[f"/{self.location}/visibility/{cur_time}"]) <= 53.0 \
                    and float(self.ndn.content_store[f"/{self.location}/pressure/{cur_time}"]) > 944.5\
                    and float(self.ndn.content_store[f"/{self.location}/wind_speed/{cur_time}"]) <= 5.0\
                    and float(self.ndn.content_store[f"/{self.location}/temperature/{cur_time}"]) <= -0.5:
                printv('Temperature is at freezing_point, spreading Anti_frost_spray.')
            else:
                pass

        except: 
            printv("Some sensor data missing. Actuation not possible.")
    
    #### ! This function was written by Stephen Rowe
    def __generate_starter_fib(self):
        # e.g. if this class is initialized with 
        #   create_drone('Cork', tasks = ['temperature', 'humidity', 'pressure'], this_interface = 'localhost:33333')
        
        # this function will generate
        # {'/': {'Cork': {'*': {'localhost:33333'}, '/': {'temperature': {'*': {'localhost:33333'}, '/': {}}, 'humidity': {'*': {'localhost:33333'}, '/': {}}, 'pressure': {'*': {'localhost:33333'}, '/': {}}}}}}
        
        # "*" is the set of accessible devices for this endpoint, e.g. "Cork"
        # "/" is a dict of children path (e.g. '/Cork/temperature'), with equivalent structure 
        
        self.this_device_paths = { "/": { self.location: { '*': { self.this_interface }, '/': {} } }}
        
        for task in self.this_sensor_tasks:
            self.this_device_paths['/'][self.location]['/'][task] = { '*': { self.this_interface }, '/': {} }
            
        printv("paths", self.this_device_paths)
            
        return self.this_device_paths