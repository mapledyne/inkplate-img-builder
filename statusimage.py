import logging
import os
import requests
import json
from PIL import Image, ImageFont, ImageDraw
import datetime
from icalevents.icalevents import events
import pytz

WHITE = 1
BLACK = 0

class StatusImage():
    def __init__(self, weatherApiKey, calendarUrl):
        super().__init__()
        self.calendarUrl = calendarUrl
        self.weatherApiKey = weatherApiKey
        self.lat = 47.608013
        self.lon = -122.335167
        self.units = "Imperial"
        self.weather = None
        self.calendar = None
        
        if self.weatherApiKey is None:
            logging.error("Weather API key is not found.")
        if self.calendarUrl is None:
            logging.error("Calendar URL is not found.")
        logging.info(f'Lat: {self.lat}, Lon: {self.lon}, Units: {self.units}')

    def getWeatherJson(self):
        logging.info('Loading Weather JSON...')
        part = "minutely,hourly,alerts"
        url = 'https://api.openweathermap.org/data/2.5/onecall?'
        url += f'lat={self.lat}&lon={self.lon}&exclude={part}&units={self.units}&appid={self.weatherApiKey}'
        result = requests.get(url)
        self.weather = json.loads(result.text)

    def getCalendarData(self):
        logging.info("Updating calendar info...")
        url = self.calendarUrl
        # result = requests.get(url)
        # print(result.text)
        # cal = result.text
        self.calendar = events(url, fix_apple=True)
        
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
            temp_range = f'{low}° — {high}°'
            temp_width = canvas.textsize(temp_range, temp_font)[0]
            temp_x = (width - temp_width) / 2
            canvas.text((temp_x + x, y + 92), temp_range, fill=BLACK, font=temp_font)
            
            # Forecast icon
            icon_width = 50
            icon = self.getWeatherIconImage(day)
            icon = icon.resize((icon_width,icon_width))
            icon_x = int(x + (width - icon_width) / 2)
            image.paste(icon, (icon_x, y + 40), icon)
    
    def findEmoji(self, test):
        for c in test:
            ord_c = ord(c)
            if ord_c >= 0x1F000 and ord_c <= 0x1FAFF:
                return c
        return ""
    
    def drawEvent(self, event, canvas, y):
        event_font = self.getFont(20)
        emoji = self.findEmoji(event.summary)
        summary = event.summary.encode('ascii', 'ignore').decode('ascii').strip()
        if event.all_day:
            time = "(All day)"
        else:
            time = f'{event.start:%-I:%M%p}'
        logging.info(f'\t{time} : {summary}')
        canvas.text((20, y + 3), time, fill=BLACK, font=event_font)
        canvas.text((110, y + 3), summary, fill=BLACK, font=event_font)
        if emoji != "":
            symbola = ImageFont.truetype('assets/symbola.otf', 25)  
            canvas.text((550, y + 3), emoji, fill=BLACK, font=symbola)
        
    def drawCalendar(self, image, canvas):
        if self.calendar is None:
            self.getCalendarData()

        y = int(275 + (600 / 5)) # bottom of forecast
        day_font = self.getFont(30)
        date_width = canvas.textsize('Today', day_font)[0]
        date_x = (600 - date_width) / 2
        canvas.text((date_x,y + 3), 'Today', fill=BLACK, font=day_font)
        canvas.line([(0, y + 50), (600, y + 50)], fill=BLACK, width=2)

        y += 55
        tz = pytz.timezone('US/Pacific')
        now = datetime.datetime.now(tz)

        evented = False
        # today all day
        logging.info("Today events:")
        for event in self.calendar:
            if event.start.date() != now.date() or not event.all_day:
                continue
            self.drawEvent(event, canvas, y)
            evented = True
            y += 40
        # today timed
        for event in self.calendar:
            if event.start.date() != now.date() or event.all_day:
                continue
            if event.start < now:
                continue
            self.drawEvent(event, canvas, y)
            evented = True
            y += 40
        if not evented:
            date_width = canvas.textsize('No Events', self.getFont(20))[0]
            date_x = (600 - date_width) / 2
            canvas.text((date_x,y + 3), 'No Events', fill=BLACK, font=self.getFont(20))
            y += 40

        # Tomorrow
        tomorrow = now + datetime.timedelta(days=1)
        canvas.line([(0, y), (600, y)], fill=BLACK, width=2)
        date_width = canvas.textsize('Tomorrow', day_font)[0]
        date_x = (600 - date_width) / 2
        canvas.text((date_x,y + 3), 'Tomorrow', fill=BLACK, font=day_font)
        canvas.line([(0, y + 50), (600, y + 50)], fill=BLACK, width=2)
        y += 50
        evented = False
        
        for event in self.calendar:
            if event.start.date() != tomorrow.date() or not event.all_day:
                continue
            self.drawEvent(event, canvas, y)
            evented = True
            y += 40
        # today timed
        for event in self.calendar:
            if event.start.date() != tomorrow.date() or event.all_day:
                continue
            self.drawEvent(event, canvas, y)
            evented = True
            y += 40

        if not evented:
            date_width = canvas.textsize('No Events', self.getFont(20))[0]
            date_x = (600 - date_width) / 2
            canvas.text((date_x,y + 3), 'No Events', fill=BLACK, font=self.getFont(20))
            y += 40
        
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

        # Calendar Items
        self.drawCalendar(img, canvas)
        
        return img

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    img = StatusImage(os.getenv("WEATHERAPI", None), os.getenv("CALENDARURL", None))
    img.getImage().save("sample.png")
