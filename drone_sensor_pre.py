
#### ! This file was written by Amit Amola
import os

class Sensor:
    def __init__(self):
        pass

    def read_csv(self, location):
        file_data = open(os.path.join('data_to_use', f'{location}.csv'))
        return file_data
    
    # def current_time(self):
    #     return str(datetime.now().replace(second=0, microsecond=0, minute=0).time())

    def get_temperature(self, location, time) -> int:
        file_data = self.read_csv(location)
        for row in file_data:
            all_vals = row.split('\n')[0].split(',')
            if all_vals[0].startswith(time):
                return all_vals[1]

    # Write same function for humidity, dew_point, pressure, wind_speed, cloudiness, visibility
    def get_humidity(self, location, time) -> int:
        file_data = self.read_csv(location)
        for row in file_data:
            all_vals = row.split('\n')[0].split(',')
            if all_vals[0].startswith(time):
                return all_vals[2]

    def get_dew_point(self, location, time) -> int:
        file_data = self.read_csv(location)
        for row in file_data:
            all_vals = row.split('\n')[0].split(',')
            if all_vals[0].startswith(time):
                return all_vals[3]
            
    def get_pressure(self, location, time) -> int:
        file_data = self.read_csv(location)
        for row in file_data:
            all_vals = row.split('\n')[0].split(',')
            if all_vals[0].startswith(time):
                return all_vals[4]
    
    def get_wind_speed(self, location, time) -> int:
        file_data = self.read_csv(location)
        for row in file_data:
            all_vals = row.split('\n')[0].split(',')
            if all_vals[0].startswith(time):
                return all_vals[5]
    
    def get_cloudiness(self, location, time) -> int:
        file_data = self.read_csv(location)
        for row in file_data:
            all_vals = row.split('\n')[0].split(',')
            if all_vals[0].startswith(time):
                return all_vals[6]

    def get_visibility(self, location, time) -> int:
        file_data = self.read_csv(location)
        for row in file_data:
            all_vals = row.split('\n')[0].split(',')
            if all_vals[0].startswith(time):
                return all_vals[7]

# def main():
#     sensor = Sensor()
#     while True:
#         loc = '52.953,-6.461'
#         tim = '06:00:00'
#         print(sensor.get_wind_speed(loc, tim))
#         break

# main()
