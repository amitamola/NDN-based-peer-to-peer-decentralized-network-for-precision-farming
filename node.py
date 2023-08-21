import ast
import get_in_range_drones
import client as c
import get_time
from format_p import *

def analyse_packet(packet):
    packet_info = packet.split('|')
    packet_type, *packet_payload = packet_info
    return packet_type, packet_payload

class Node:
    #### ! This function was written by Mingzhe Liu & Stephen Rowe
    def __init__(self, this_interface, fib_mutex_lock, wireless_connections, drone_range):
        self.this_interface = this_interface
        # key: name of data; value: data
        # { name: data }
        # eg. {'/Cork/dew/14:15-14:20': '123'}
        self.content_store = {}
        # {'name': {'requesting_interfaces': {'requester 1', 'requester 2' }}}
        # eg. {'/Cork/dew/14:15-14:20': {'requesting_interfaces': { '10.35.70.20:33402','10.35.70.21:33402' }}}
        self.pending_table = {}
        # This var records what interest I(this node) have sent.
        # When a data packet comes back, I can tell if that's what I want
        # ('name': '')
        
        # This var is deprecated
        # self.interest_sent = {}

        # FIB-related
        self.forwarding_information_base = {}
        self.fib_mutex_lock = fib_mutex_lock
        self.fib_updates_pending = 0

        self.wireless_connections = wireless_connections
        self.drone_range = drone_range

    def send_packet(self, packet, destination):
        try:
            c.Client().send(self.this_interface, destination, packet)
        except:
            pass

    #### ! This function was written by Mingzhe Liu
    def receive_packet(self, packet, source):
        head, body = analyse_packet(packet)
        if head == 'Interest':
            self.__query_cs(packet, source)
        elif head == 'Data':
            if body[0] == 'Advertise':  # If an endpoint is advertising what data is available to it
                self.update_fib(other_fib=ast.literal_eval(body[1]), other_interface=source)
            else:
                printv(f'querying {self.this_interface} pit for {packet} from {source}')
                self.__query_pit(packet, source)
                
    #### ! This function was written by Mingzhe Liu & Stephen Rowe
    def __query_pit(self, packet, source):
        head, body = analyse_packet(packet)
        if head == 'Interest':
            # Add this interest to PIT
            name = body[0]
            if name in self.pending_table:
                self.pending_table[str(name)]['requesting_interfaces'].add(str(source))
                printv(f'recieved {packet}, but we have already forwarded this request. Adding {source} to list of requesting interfaces for this Interest packet, while waiting for data')
            else:
                try:
                    self.fib(packet)
                    self.pending_table[name] = { 'requesting_interfaces': set( [source]) }
                    printv(f'recieved {packet}, but we cannot satisfy it with our CS. Forwarding packet...')
                except Exception as e:
                    printv(e)
                
        elif head == 'Data':
            name, data = body[0], body[1]
            self.__query_cs(packet, source)
            if name in self.pending_table:
                # Send the data to all those who had asked before, and cache that to cs.
                printv(f'a previously requested packet, {packet}, has been delivered by {source}, sending packet to drones that previously requested it { self.pending_table[name]["requesting_interfaces"] }')
                for destination in self.pending_table[name]['requesting_interfaces']:
                    if destination == source:
                        continue
                    self.send_packet(packet, destination)
                try:
                    self.pending_table.pop(name)
                except: 
                    pass

    #### ! This function was written by Mingzhe Liu
    def __query_cs(self, packet, source):
        # Only interest packet coming
        head, body = analyse_packet(packet)
        if head == 'Interest':
            name = body[0]
            if name in self.content_store:
                # build a packet with the data
                printv(f'{packet} found in content store, sending it back to {source}')
                packet = 'Data|' + name + '|' + self.content_store[name]
                self.send_packet(packet, source)
            else:
                self.__query_pit(packet, source)
        elif head == 'Data':
            # Save this data to CS
            if body[0] in self.content_store:
                printv(f"already have {body[0]} in content store, ignored")
                self.clean_cs()
                return
            printv(f'adding {packet} to content store')
            self.content_store[body[0]] = body[1]
            printv(f"CS now looks like {self.content_store}")
        self.clean_cs()

    #### ! This function was written by Mingzhe Liu
    def clean_cs(self):
        # This is used to clean content store based on the time included in the name,
        # If it's invalid, this will pop it from content store.
        # Every time __query_cs() finishes executing, this function will execute once.
        current_time = str(get_time.get_time())
        temp_content_store = {}
        for name in self.content_store:
            temps = name.split('/')
            if temps[-1] == current_time:
                temp_content_store[name] = self.content_store[name]
        self.content_store = temp_content_store

    #### ! This function was written by Stephen Rowe
    def fib(self, packet):
        # Assuming this is an interest packet
        head, name = analyse_packet(packet)

        if head != 'Interest':
            raise Exception("You're passing something that isn't a Interest packet to the FIB :", packet)
        
        if type(name) == list and len(name) == 1:
            name = name[0]
        else:
            raise Exception("something funky here, take a look")

        search = name.split('/') # /Cork/temperature/time -> ['Cork', 'temperature', 'time']

        self.refresh_fib()  # make sure our FIB is up-to-date

        fib = self.forwarding_information_base.copy()
        interfaces_to_send_to = {}
        
        try:
            for path in search:
                if path == '':
                    continue
                if path in fib['/'] and fib['/'][path]['*'] != { self.this_interface }:
                    fib = fib['/'][path]
                else:
                    interfaces_to_send_to = fib['*'].copy()
        except:
            raise Exception(f"No valid route currently available for {name} in {self.forwarding_information_base}")

        try:
            interfaces_to_send_to.remove(self.this_interface)
        except:
            pass    # if self.this_interface is *not* in interfaces_to_send_to here, this is fine

        if len(interfaces_to_send_to) == 0:
            raise Exception(f"No valid route currently available for '{name}' in {self.forwarding_information_base}")
        
        printv(f'{self.this_interface} is sending {packet} to {interfaces_to_send_to}')

        for interface in interfaces_to_send_to:
            self.send_packet(packet, interface)

    #### ! This function was written by Stephen Rowe
    def refresh_fib(self):
        self.fib_mutex_lock.acquire()
        connected_devices = self.clear_inaccessible_endpoints_from_fib()
        self.fib_mutex_lock.release()
        self.advertise_available_data_to_connected_devices(connected_devices)

    #### ! This function was written by Stephen Rowe
    def update_fib(self, other_fib, other_interface):
        self.fib_updates_pending += 1
        self.fib_mutex_lock.acquire()
        self.__update_fib_recursive(fib1 = self.forwarding_information_base, fib2 = other_fib, other_interface = other_interface)
        connected_devices = self.clear_inaccessible_endpoints_from_fib()
        self.fib_updates_pending -= 1
        self.fib_mutex_lock.release()
        printv("FIB for", self.this_interface, "is now", self.forwarding_information_base)
        self.advertise_available_data_to_connected_devices(connected_devices)

    #### ! This function was written by Stephen Rowe
    def __update_fib_recursive(self, fib1, fib2, other_interface):
        for path in fib2.keys():
            if path in fib1['/']:
                fib1['/'][path]['*'].add(other_interface)
            else:
                fib1['/'][path] = { '*': { other_interface }, '/': {} }

            if self.this_interface in fib1['/'][path]['*']:
                self.__update_fib_recursive(fib1['/'][path], fib2[path], other_interface)

    #### ! This function was written by Stephen Rowe
    def get_all_known_data_endpoints(self):
        known = {}
        if self.forwarding_information_base != {}:
            self.__get_all_known_data_endpoints_recursive(self.forwarding_information_base, known)
        return known

    #### ! This function was written by Stephen Rowe
    def __get_all_known_data_endpoints_recursive(self, fib, known):
        if fib['/'] == {}:
            return

        for path in fib['/'].keys():
            known[path] = {}
            self.__get_all_known_data_endpoints_recursive(fib['/'][path], known[path])

    #### ! This function was written by Stephen Rowe
    def clear_inaccessible_endpoints_from_fib(self):
        if self.forwarding_information_base == {}:
            return
        connected_devices_set = set(get_in_range_drones.get_in_range_drones(self.this_interface, self.wireless_connections.tracker, self.drone_range))
        connected_devices_set.add(self.this_interface)
        self.__clear_inaccessible_recursive(self.forwarding_information_base, connected_devices_set)
        connected_devices_set.remove(self.this_interface)
        return connected_devices_set

    #### ! This function was written by Stephen Rowe
    def __clear_inaccessible_recursive(self, fib, connected_devices):
        for path in fib['/'].copy().keys():
            updated_interfaces = connected_devices.intersection(fib['/'][path]['*'])
            fib['/'][path]['*'] = updated_interfaces
            if len(updated_interfaces) == 0:
                del fib['/'][path]
            else:
                self.__clear_inaccessible_recursive(fib['/'][path], connected_devices)

    #### ! This function was written by Stephen Rowe
    def advertise_available_data_to_connected_devices(self, connected_devices):
        # Need to decide if we need to tell the other devices we're currently connected to about the data endpoints that
        # this device has (some) access to. This is done by 
        # (i)   seeing if we're connected to a device we weren't connected to before
        # (ii)  seeing if the FIB is being updated by another thread at the moment (we should wait until 
        #       that update is done so we're not inundating other devices with useless updates) 
        # (iii) seeing if this device actually does know about some new endpoints that it didn't before. 
        #       Otherwise, an update would be useless

        updated_known_endpoints = self.get_all_known_data_endpoints()

        try: # don't worry about it
            self.previously_connected_devices
        except:
            self.previously_connected_devices = set()

        try: # don't worry about it
            self.known_endpoints
        except:
            self.known_endpoints = dict()
            
        if not connected_devices:
            connected_devices = set()

        self.known_endpoints = updated_known_endpoints
        newly_connected_devices = connected_devices.difference(self.previously_connected_devices)
        self.previously_connected_devices = connected_devices
        # If there's a newly connected device we have to tell it what endpoints we know.
        if len(newly_connected_devices) > 0 and self.known_endpoints == updated_known_endpoints:
            self.__send_advertisement(newly_connected_devices)
            return

        # if another thread is currently updating the FIB, we shouldn't send an advertisement until that is done
        if self.fib_updates_pending != 0:
            return

        # if this device knowns about new endpoints, we have to tell all directly connected endpoints
        if self.known_endpoints != updated_known_endpoints:
            self.known_endpoints = updated_known_endpoints
            self.__send_advertisement(connected_devices)

    #### ! This function was written by Stephen Rowe
    def __send_advertisement(self, interfaces_to_send_to):
        packet = f'Data|Advertise|{self.known_endpoints}'
        for interface in interfaces_to_send_to:
            self.send_packet(packet, interface)