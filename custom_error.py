
#### ! This file was written by Stephen Rowe

class CustomConnectionError(Exception):
    def __init__(self, other_interface, host, port):
        self.other_interface = other_interface
        self.host = host
        self.port = port