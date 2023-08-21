import datetime

def get_time():
    a = datetime.datetime.now()
    return "{:02d}".format(a.minute % 24)