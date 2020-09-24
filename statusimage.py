import logging
import os
import requests
import json
from PIL import Image, ImageFont, ImageDraw
import datetime

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
        if self.weatherApiKey is None:
            logging.error("Weather API key is not found.")
        logging.info(f'Lat: {self.lat}, Lon: {self.lon}, Units: {self.units}')

    def getWeatherJson(self):
        logging.info('Loading Weather JSON...')
        part = "minutely,hourly,alerts"
        url = 'https://api.openweathermap.org/data/2.5/onecall?'
        url += f'lat={self.lat}&lon={self.lon}&exclude={part}&units={self.units}&appid={self.weatherApiKey}'
        result = requests.get(url)
        self.weather = json.loads(result.text)

    def getForecastDay(self, day=0):
        date = self.weather['daily'][day]['dt']
        date = datetime.datetime.utcfromtimestamp(date)
        logging.info(f'Forecast date: {date} ({date:%a})')
        
        return f'{date:%a}'

    def getWeatherTemps(self, day=0):
        if self.weather is None:
            self.getWeatherJson()
        
        temp = int(round(self.weather['current']['temp']))
        low = int(round(self.weather['daily'][day]['temp']['min']))
        high = int(round(self.weather['daily'][day]['temp']['max']))
        pop = int(round(self.weather['daily'][day]['pop'] * 100))

        logging.info(f'getWeatherTemps (day={day}): {temp}, {low}, {high}, {pop}')
        return (temp, low, high, pop)

    def getWeatherIcon(self, day=0):
        if self.weather is None:
            self.getWeatherJson()
        icon = self.weather['daily'][day]['weather'][0]['icon']
        logging.info(f'getWeatherIcon: {icon}')
        return icon      

    def getWeatherIconImage(self, day=0):
        icon = self.getWeatherIcon(day)
        img = Image.open(f'assets/{icon}.png')
        return img

    def getFont(self, size):
        return ImageFont.truetype('assets/futura.ttc', size)   

    def drawForecast(self, image, canvas):
        y = 275
        width = 600 / 5
        height = width
        canvas.line([(0, y), (600, y)], fill=BLACK, width=2)
        canvas.line([(0, y+height), (600, y+height)], fill=BLACK, width=2)

        day_name_font = self.getFont(30)
        temp_font = self.getFont(20)
        for day in range(1,6):
            x = int(width * (day - 1))
            logging.info(f'Forecast, day: {day}. Starting x: {x}')
            day_name = self.getForecastDay(day)
            
            if x > 1:
                canvas.line([(x, y), (x, y+height)], fill=BLACK, width=2)
            
            # Day names
            date_width = canvas.textsize(day_name, day_name_font)[0]
            date_x = (width - date_width) / 2
            canvas.text((date_x + x, y + 3), day_name, fill=BLACK, font=day_name_font)

            # temp forecast
            temp, low, high, pop = self.getWeatherTemps(day)
            temp_range = f'{low}° - {high}°'
            temp_width = canvas.textsize(temp_range, temp_font)[0]
            temp_x = (width - temp_width) / 2
            canvas.text((temp_x + x, y + 95), temp_range, fill=BLACK, font=temp_font)
            
            # Forecast icon
            icon_width = 50
            icon = self.getWeatherIconImage(day)
            icon = icon.resize((icon_width,icon_width))
            icon_x = int(x + (width - icon_width) / 2)
            image.paste(icon, (icon_x, y + 40), icon)

    def getImage(self):
        img = Image.new("1", (600, 800), WHITE)
        canvas = ImageDraw.Draw(img)
        
        fontDefault = self.getFont(40)
        
        # Draw current date:        
        canvas.rectangle((0,0,600,55), fill=BLACK)
        today = datetime.datetime.today()
        current_date = f'{today:%A, %B %d}'
        date_width = canvas.textsize(current_date, fontDefault)[0]
        date_x = (600 - date_width) / 2
        canvas.text((date_x,3), current_date, fill=WHITE, font=fontDefault)
        
        # Draw current conditions:
        weather = self.getWeatherIconImage()
        img.paste(weather, (25, 60), weather)
        temp, low, high, pop = self.getWeatherTemps()
        
        canvas.text((300, 30), f'{temp}°', font=self.getFont(150))

        currentFont = self.getFont(25)
        icon = Image.open(f'assets/temp-low.png')
        icon = icon.resize((50,50))
        img.paste(icon, (250, 200), icon)
        icon = Image.open(f'assets/temp-high.png')
        icon = icon.resize((50,50))
        img.paste(icon, (350, 200), icon)
        icon = Image.open(f'assets/umbrella.png')
        icon = icon.resize((50,50))
        img.paste(icon, (450, 200), icon)

        canvas.text((300, 210), f'{low}°', font=currentFont)
        canvas.text((400, 210), f'{high}°', font=currentFont)
        canvas.text((500, 210), f'{pop}%', font=currentFont)

        # Forecast dates        
        self.drawForecast(img, canvas)

        return img

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    img = StatusImage(os.getenv("WEATHERAPI", None))
    img.getImage().save("sample.png")
