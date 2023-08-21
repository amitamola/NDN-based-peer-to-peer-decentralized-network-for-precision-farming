
#### ! This file was written by Stephen Rowe

import socket
import threading
import time
import custom_error as er
class Client(threading.Thread):
    def send(self, this_interface, other_interface, packet, packets = []): # send either 1 packet (packet : string) or an array of packets ( packets : list )
        host, port = other_interface.split(':')
        
        attempts_made = 0
        connection_success = False
        
        while attempts_made < 2:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, int(port)))
                connection_success = True
                break
            except socket.error:
                attempts_made += 1
                time.sleep(0.2)
                
        if not connection_success:
            raise er.CustomConnectionError(other_interface, host, port)
            
        total_packet_content = ''

        # immediate connection interface data, required for PIT
        sock.sendall(str.encode('INTERFACE|{}\n'.format(this_interface)))  
        
        if len(packets) > 0:
            total_packet_content = '\n'.join(packets)  # concatenate all packets into a \n delimited string so they can be separated on the other end
        else:
            total_packet_content = packet
            
        sock.sendall(str.encode(total_packet_content)) 
        sock.close()
            
    # Unused
    def ping(self, other_interface):
        host, port = other_interface.split(':')
        try: 
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
            return True
        except:
            return False