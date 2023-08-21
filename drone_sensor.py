
#### ! This file was written by Mingzhe Liu
import requests
import json
import time
import random


def get_api_values(location):
    url = 'https://api.openweathermap.org/data/2.5/weather?q=' + \
          location + '&appid=81a0a46feff393c3568d9415b51211da'
    print("URL", url)
    response = requests.get(url)
    print(response)
    if response.status_code == 200:
        # return data with json format
        content = json.loads(response.content)
        return content
    else:
        return None


class Sensor:
    def __init__(self):
        self.last_request_time = 0
        self.last_temp = 0
        self.last_humidity = 0
        self.last_pressure = 0
        self.last_wind = None
        self.last_location = ''
        self.time_gap = 5 * 60 * 1000

    def get_temperature(self, location) -> int:
        """
        Params:
            location: This should be inputted as a city name, but it is pretending as a geo location(long:/lati:)
        """
        if ((time.time() - self.last_request_time) > self.time_gap) or (location != self.last_location):
            content = get_api_values(location).get('main').get('temp')
            self.last_temp = content
            self.last_request_time = time.time()
            return content
        else:
            return self.last_temp + random.randint(-2, 2)

    def get_humidity(self, location) -> int:
        """
        Params:
            location: This should be inputted as a city name, but it is pretending as a geo location(long:/lati:)
        """
        if (time.time() - self.last_request_time) > self.time_gap or (location != self.last_location):
            content = get_api_values(location).get('main').get('humidity')
            self.last_humidity = content
            self.last_request_time = time.time()
            return content
        else:
            res = self.last_humidity + random.randint(-5, 5)
            if res > 0:
                return res
            else:
                return 0

    def get_pressure(self, location) -> int:
        """
        Params:
            location: This should be inputted as a city name, but it is pretending as a geo location(long:/lati:)
        """
        if (time.time() - self.last_request_time) > self.time_gap or (location != self.last_location):
            content = get_api_values(location).get('main').get('pressure')
            self.last_pressure = content
            self.last_request_time = time.time()
            return content
        else:
            res = self.last_pressure + random.randint(-50, 50)
            if res > 0:
                return res
            else:
                return 0

    def get_wind(self, location):
        """
        Params:
            location: This should be inputted as a city name, but it is pretending as a geo location(long:/lati:)
        Return:
            The speed of wind, the degree of wind.
        """
        if (time.time() - self.last_request_time) > self.time_gap or (location != self.last_location):
            content = get_api_values(location).get('wind')
            self.last_wind = content
            self.last_request_time = time.time()
            self.last_location = location
            return content.get('speed'), content.get('deg')
        else:
            speed = self.last_wind.get('speed') + random.randint(-1, 1)
            if speed > 0:
                return speed, self.last_wind.get('deg') + random.randint(-20, 20)
            else:
                return 0, self.last_wind.get('deg') + random.randint(-20, 20)

# def main():
#     sensor = Sensor()
#     while True:
#         message = input()
#         print(sensor.get_wind(message))