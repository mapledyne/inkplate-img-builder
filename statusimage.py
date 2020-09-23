import logging
import os
import requests
import json
from PIL import Image

WHITE = 1
BLACK = 0

class StatusImage():
    def __init__(self, weatherApiKey):
        super().__init__()
        self.weatherApiKey = weatherApiKey
        self.lat = 47.608013
        self.lon = -122.335167
        self.units = "Imperial"
        self.weather = None

    def getWeatherJson(self):
        part = "minutely,hourly,alerts"
        url = 'https://api.openweathermap.org/data/2.5/onecall?'
        url += f'lat={self.lat}&lon={self.lon}&exclude={part}&units={self.units}&appid={self.weatherApiKey}'
        result = requests.get(url)
        self.weather = json.loads(result.text)
        
    def getWeatherTemp(self):
        if self.weather is None:
            self.getWeatherJson()
        
        return self.weather['current']['temp']

    def getWeatherIcon(self):
        if self.weather is None:
            self.getWeatherJson()
        
        return self.weather['current']['weather'][0]['icon']        

    def getImage(self):
        img = Image.new("1", (600, 800), WHITE)
        img.save("sample.png")

if __name__ == "__main__":
    logging.warning("Hello")
    img = StatusImage(os.getenv("WEATHERAPI", None))
    
    logging.warning(f'API: {img.weatherApiKey}')
    print(img.getWeatherTemp())
    print(img.getWeatherIcon())
    img.getImage()
