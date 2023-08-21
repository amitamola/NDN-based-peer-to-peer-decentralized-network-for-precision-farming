import re
import os
from datetime import datetime

def printv(*strings):
    string = ' '.join(str(s) for s in strings)
    msg = re.sub(r"\d\d\.\d\d\.\d\d\.(\d\d):\d\d(\d\d\d)", r"D\1-\2", string)
    pid = str(os.getppid()) + '_' + str(os.getpid())
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    try: 
        out = open(f'drone_output/{pid}.txt', 'a')
        out.write(f'{current_time}: {msg}\n\n')
    except:
        out = open(f'drone_output/{pid}.txt', 'w')
        out.write(f'{current_time}: {msg}\n\n')
    print(msg)