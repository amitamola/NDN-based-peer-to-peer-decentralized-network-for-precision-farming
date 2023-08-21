
#### ! This file was written by Stephen Rowe

import numpy as np
import time
import get_in_range_drones as geo
import argparse
import threading
import ast
import server as s
import create_drone as cd
import node as ndn
from format_p import *

class wireless_connections:
    def __init__(self):
        self.tracker = {}

prob_movement = [0.05, 0.95]  # probability of movement for random walk algorithm

#Variables for holding information about connections
connections = []
connection_count = 0

def get_probabilities(self, current_value):
    # Drone movement is based on Random Walk algorithm, in which the decision to move / not move
    # in X or Y coordinates is determined by prob array below. If the device will move, it will 
    # go to an adjacent coordinate.
    rr = np.random.random()
    downp = rr < prob_movement[0]
    upp = rr > prob_movement[1]
    down = downp and current_value > 0
    up = upp and current_value < self.area_dimensions
    return down, up

class Drone:    
    def __init__(self, args):
        self.x = np.random.randint(0, int(args.area_dimensions))
        self.y = np.random.randint(0, int(args.area_dimensions))
        self.drone_range = args.drone_range
        self.area_dimensions = args.area_dimensions
        self.wireless_connections = wireless_connections()
        self.outfile = args.outfile
        
        self.server = s.Server(
            host = args.host, 
            port = args.port,
        )
        
        # Don't do anything else until this drone has found a port
        while not self.server.port_found:
            pass 
        
        self.host = self.server.host
        self.port = self.server.port
        self.this_interface = "{}:{}".format(self.host, self.port)
        
        print(f'SUBPROCESS|{self.host}:{self.port}')
        
        printv('{}: [{},{}]'.format(self.this_interface, self.x, self.y))
        
        self.update_drone_info(self.x, self.y)
        
        threading.Thread(target = self.read_input).start()

        self.fib_mutex_lock = threading.Lock()
        
        self.ndn = ndn.Node(
            this_interface = self.this_interface, 
            fib_mutex_lock = self.fib_mutex_lock, 
            wireless_connections = self.wireless_connections, 
            drone_range = self.drone_range
        )
         
        self.functionality = cd.create_drone(this_sensor_tasks = args.tasks, location = args.location, this_interface = self.this_interface, ndn = self.ndn)
        
        self.server.start_server(self.ndn)
        
    def move(self):
        down, up = get_probabilities(self, self.y)
        new_y = self.y - down + up
        
        down, up = get_probabilities(self, self.x)
        new_x = self.x - down + up

        if new_y == self.y and new_x == self.x:
            return
        
        printv('{}: [{},{}] -> [{},{}]'.format(self.this_interface, self.x, self.y, new_x, new_y))
        self.x = new_x
        self.y = new_y        
        self.update_drone_info(self.x, self.y)
        printv(self.this_interface, ' CAN COMMUNICATE WITH ', geo.get_in_range_drones(self.this_interface, self.wireless_connections.tracker, self.drone_range))
        
    def update_drone_info(self, new_x, new_y):
        self.wireless_connections.tracker[self.this_interface] = { 'x': new_x, 'y': new_y }
        
        print('UPDATE_COORDS|{}|{}'.format(self.this_interface, self.wireless_connections.tracker[self.this_interface])) # tell master process to update table
        
    # used so master process can communicate with subprocesses
    def read_input(self): 
        file = open('outfiles/' + self.outfile, 'r')
        while True:
            line = file.readline()
            if(line):
                self.wireless_connections.tracker = ast.literal_eval(line)
                self.ndn.refresh_fib()
            
parser = argparse.ArgumentParser()
parser.add_argument('-r', '--drone_range', required=True, type=int)
parser.add_argument('-a', '--area_dimensions', required=True, type=int)
parser.add_argument('-i', '--host', required=True)
parser.add_argument('-p', '--port', required=True, type=int)
parser.add_argument('-f', '--outfile', required=True)
parser.add_argument('-t', '--tasks', required=True, help="a set of sensors this drone has")
parser.add_argument('-l', '--location', required=True, type=str)
args = parser.parse_args()

drone = Drone(args)

while True:
    drone.move()
    time.sleep(2)