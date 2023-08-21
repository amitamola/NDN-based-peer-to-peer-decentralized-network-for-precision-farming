
#### ! This file was written by Stephen Rowe

import socket
import threading
from format_p import *
import traceback

class ServersClient(threading.Thread):
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
        # while self.signal:
        try:
            data = self.new_socket.recv(99999)
            if data != "":
                transmitted_data = str(data.decode("utf-8"))
                
                # packets sent from Client to Server are INTERFACE|ip:port followed by a number of NDN packets
                # These are split with \n
                connection_interface, *packets = transmitted_data.split('\n')
                                                
                # INTERFACE|ipaddress:port
                check_interface, sender_interface = connection_interface.split('|')
                
                for packet in packets:
                    if len(packet) == 0:
                        continue
                    printv(f'Recieved packet from {sender_interface}: {packet}')
                    self.server.ndn.receive_packet(packet, sender_interface)
        except Exception as e: 
            printv(''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)))
            self.server.connections.remove(self)
            self.server.connection_count -= 1            
class Server():
    #Wait for new connections
    def new_connection(self, socket):
        while True:
            sock, address = socket.accept()
            connected_client = ServersClient(
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

    def start_server(self, ndn):
        self.ndn = ndn
        #Create new thread to wait for connections
        connection_thread = threading.Thread(target = self.new_connection, args = (self.new_socket,))
        connection_thread.start()
        self.ndn.refresh_fib()