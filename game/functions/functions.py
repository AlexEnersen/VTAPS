
import numpy as np
import os
import random
import watchtower, logging

environment = os.environ['ENV']


if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

monthRanges = [32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 367]

def forecastWeather(weather_text):  

    forecast_text = []

    for line in weather_text:
        items = list(filter(None, line.split(" ")))

        if len(items) < 1:
            continue

        weatherDate = items[0]

        if not weatherDate.isnumeric():
            continue

        srad = str(round(float(items[1]), 1))
        high = round(float(items[2]), 1)
        low = round(float(items[3]), 1)
        rain = round(float(items[4]), 1)
            
        high_forecast = str(round(forecastTemp(high), 1))
        low_forecast = str(round(forecastTemp(low), 1 ))
        rain_forecast = str(abs(round(forecastRain(rain), 2)))

        weather_string = weatherDate + " " + srad + " " + high_forecast + " " + low_forecast + " " + rain_forecast + "\n"
        
        forecast_text.append(weather_string)

    return "".join(forecast_text)

def forecastTemp(temp):
    value = random.uniform(temp-2, temp+2)
    return(value)

def forecastRain(rain):
    value = random.uniform(rain-1, rain+1)
    if value < 0:
        value = 0
    return(value)

def changeWeatherYear(weatherText, year):
    newText = []
    for line in weatherText:
        items = line.split(" ")
        items = [x for x in items if x]
        if len(items) == 0 or not items[0].isnumeric():
            newText.append(line)
            continue
        newDate = str(year) + items[0][4:7]
        newLine = newDate + line[7:]
        newText.append(newLine)
    return newText