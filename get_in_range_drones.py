
#### ! This file was written by Amit Amola & Stephen Rowe
import numpy as np

def get_in_range_drones(this_interface, wireless_connections, drone_range):
     # making a copy since this dict will be modified in this function, but there may be scenarios 
     # where multiple threads are reading from the same dict
     
     all_drones = wireless_connections.copy()
     this_drone = all_drones.pop(this_interface)
     this_drone_info = tuple([this_drone['x'], this_drone['y']])
    
     ids = np.array(list(all_drones.keys()))
     coords = np.array(list(map(lambda val:(val['x'],val['y']), list(all_drones.values()))))
     
     distances = np.array([np.linalg.norm(this_drone_info - c) for c in coords])
     return list(ids[np.where(distances <= drone_range)])

def is_in_range(this_interface, other_interface, wireless_connections, drone_range):
     this_drone = wireless_connections[this_interface]
     other_drone = wireless_connections[other_interface]
     this_drone_coords = np.array([this_drone['x'], this_drone['y']])
     other_drone_coords = np.array([other_drone['x'], other_drone['y']])
     res = np.linalg.norm(this_drone_coords - other_drone_coords)
     return res < drone_range