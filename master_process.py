
#### ! This file was written by Stephen Rowe
import threading
import argparse
import subprocess
import os
import ast
import client as c
import socket
import threading
import custom_error as er
import get_initial_task_vals as tasks
from format_p import *

wireless_connections = {}
wireless_connections_lock = threading.Lock()
wireless_connections_previous = {}
all_processes = {}
subprocess_interfaces = set()
pi_interfaces = set()
this_interface = None

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--count', help='number of drones to generate', type=int)
parser.add_argument('-r', '--drone_range', default=4)
parser.add_argument('-a', '--area_dimensions', default=10)
parser.add_argument('-i', '--host', default="localhost")
parser.add_argument('-p', '--port', default=33400, help='each drone will be assigned a port, starting from this number')
parser.add_argument('-o', '--other_pis', default={})
parser.add_argument('-f', '--outfile', required=True)
parser.add_argument('-l', '--location', default="52.953,-6.461")

args = parser.parse_args()
print('Creating', args.count, 'processes, each is a drone endpoint')

if args.other_pis:   
    pi_interfaces = set(ast.literal_eval(args.other_pis))

def notify_subprocesses_and_other_pis():
    msg = '{}\n'.format(wireless_connections)
    msg = msg.rstrip('\x00')
    
    out = open('outfiles/' + args.outfile, 'a')
    out.write(msg)
    out.flush()
    
    pi_interfaces_to_send_to = list(pi_interfaces)
    print(pi_interfaces_to_send_to)
    own_wireless_connections = str({k: v for k, v in wireless_connections.items() if k in subprocess_interfaces})
    
    for other_pi in pi_interfaces_to_send_to:
        try:
            c.Client().send(this_interface, other_pi, own_wireless_connections)
        except er.CustomConnectionError as e:
            remove_lost_connections(e)
            
def remove_lost_connections(e):
    print(f'removing lost connection {e.other_interface}')
    
    try: 
        pi_interfaces.remove(e.other_interface)
    except:
        return  # this interface has been removed already (by another thread)
    
    wireless_connections_lock.acquire()
    original = wireless_connections.copy()
    interfaces = list(wireless_connections.keys())
    for k in interfaces:
        if k.startswith(e.host):
            del wireless_connections[k]
    wireless_connections_lock.release()
    if original != wireless_connections:
        notify_subprocesses_and_other_pis()

# This is a modified version of server.py and client.py to suit master_process, to allow for communication between Pis
#  Ideally I'd have refactored this into server.py and client.py, but just want to get it working. 
class ProcessServersClient(threading.Thread):
    def __init__(
        self, 
        socket, 
        address,
        signal, 
        server
    ):
        threading.Thread.__init__(self)
        self.new_socket = socket
        self.address = address
        self.signal = signal
        self.server = server
    
    def __str__(self):
        return str(self.address)

    def run(self):
        global wireless_connections
        global wireless_connections_lock
        global wireless_connections_previous
        try:
            data = self.new_socket.recv(99999)
            if data != "":
                transmitted_data = str(data.decode("utf-8"))                
                pi_interface_info, new_wireless_connection_info = transmitted_data.split('\n')
                check_interface, sender_interface = pi_interface_info.split('|')
                pi_interfaces.add(sender_interface)
                
                recieved_wireless_connections_info = ast.literal_eval(new_wireless_connection_info)
                
                wireless_connections_lock.acquire()
                wireless_connections.update(recieved_wireless_connections_info)
                wireless_connections_lock.release()
                
        except Exception as e: 
            print('PROCESSSERVERSCLIENT ERROR', e)
            print("Client " + str(self.address) + " has disconnected")
            self.server.connections.remove(self)
            self.server.connection_count -= 1            

class ProcessServer():
    #Wait for new connections
    def new_connection(self, socket):
        while True:
            sock, address = socket.accept()
            connected_client = ProcessServersClient(
                socket = sock,
                address = address,
                signal = True,
                server = self,
            )
            self.connections.append(connected_client)
            connected_client.start()
            self.connection_count += 1

    def __init__(self, host, port):
        self.connections = []
        self.connection_count = 0   
        self.host = host
        self.port = port
        
        # If the port provided isn't available, find one
        self.port_found = False
        
        while not self.port_found:
            try:
                self.new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.new_socket.bind((self.host, self.port))
                self.new_socket.listen(5)
                self.port_found = True
                self.port = self.port
            except:
                self.port += 1

    def start_server(self):
        #Create new thread to wait for connections
        connection_thread = threading.Thread(target = self.new_connection, args = (self.new_socket,))
        connection_thread.start()

def create_drone_process(drone_index, args, drone_tasks):
    # This function creates a new subprocess for a drone, then ensures the stdout of that
    # drone is printed to the stdout of this script.
    os.environ['PYTHONUNBUFFERED'] = '1'
    process = subprocess.Popen(["python3", "drone.py", 
                                "--drone_range", str(args.drone_range),
                                "--area_dimensions", str(args.area_dimensions),
                                "--host", str(args.host),
                                "--port", str(int(args.port) + drone_index),
                                "--outfile", args.outfile,
                                "--tasks", str(drone_tasks),
                                "--location", str(args.location)
                                ], stdout=subprocess.PIPE, env=os.environ)
    all_processes[str(drone_index)] = process
    
    while process.poll() is None:
        out = process.stdout.readline().decode('UTF-8')
        
        if(out.startswith('UPDATE_COORDS')):
            msg = out.split('|')
            wireless_connections_lock.acquire()
            wireless_connections_previous = wireless_connections.copy()
            wireless_connections[msg[1]] = ast.literal_eval(msg[2])
            wireless_connections_lock.release()
            
            # If not all drones are on the all_drones_info object yet, then we'll hold off on sharing this. This is just to handle an FIB bug.
            if len(wireless_connections.keys()) >= args.count and wireless_connections != wireless_connections_previous:
                notify_subprocesses_and_other_pis()
        elif(out.startswith('SUBPROCESS')):
            # Method of registering subprocess data with master_process instance
            msg = out.replace('\n', '').split('|')
            subprocess_interfaces.add(msg[1])
            pass
        else:    
            print(out, end='')
        
out = open('outfiles/' + args.outfile, 'w')
out.close()

server = ProcessServer(host=str(args.host), port=int(args.port))
while not server.port_found:
    pass    # wait for port to be found before doing anything

this_interface = f'{server.host}:{server.port}'
print('THIS INTERFACE', this_interface)

server.start_server()

drone_tasks = tasks.get_sensor_tasks()

for x in range(0, int(args.count)):
    threading.Thread(target = create_drone_process, args = (x, args, drone_tasks[x % len(drone_tasks)])).start() 
    
# threading.Thread(target = endpoint_connection_checker).start()