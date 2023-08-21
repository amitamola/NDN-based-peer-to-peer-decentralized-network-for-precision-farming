
#### ! This file was written by Amit Amola
import random

sensor = ['temperature', 'humidity', 'pressure', 'wind_speed', 'cloudiness', 'visibility', 'dew_point']

def get_sensor_tasks():
    seq = sensor
    """Creates 5 unique lists of 4 sensor task each."""
    random.shuffle(seq)
    val = [seq[i:i+4] for i in range(len(seq)-3)]
    final_val = [m[i] for i,m in enumerate(val)]
    val.append(final_val)
    final = [tuple(lis) for lis in val]
    return final
