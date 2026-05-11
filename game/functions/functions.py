
import numpy as np
import os
import watchtower, logging

environment = os.environ['ENV']


if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

monthRanges = [32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 367]

def forecastWeather(weather_text):  

    lowArray = []
    highArray = []
    rainArray = []
    forecast_text = []

    for line in weather_text:
        items = list(filter(None, line.split(" ")))

        if len(items) < 1:
            continue

        weatherDate = items[0]

        if not weatherDate.isnumeric():
            continue
            
        weatherDay = weatherDate[len(weatherDate) - 3:]

        # high = str(round(float(items[2]) * (9/5) + 32, 1))
        # low = str(round(float(items[3]) * (9/5) + 32, 1))
        # rain = str(round(float(items[4])))
        srad = str(round(float(items[1]), 1))
        high = str(round(float(items[2]), 1))
        low = str(round(float(items[3]), 1))
        rain = str(round(float(items[4]), 1))

        # highArray.append(round((float(items[2]) * (9/5)) + 32, 1))
        # lowArray.append(round((float(items[3]) * (9/5)) + 32, 1))
        # rainArray.append(float(items[4].strip()))

        # if len(lowArray) >= 21:
        #     highArray.pop(0)
        #     lowArray.pop(0)
        #     rainArray.pop(0)
            
        # high_forecast = str(round(forecastData(highArray), 1))
        # low_forecast = str(round(forecastData(lowArray), 1 ))
        # rain_forecast = str(abs(round(forecastData(rainArray), 2)))
        
        # if high_forecast < low_forecast:
        #     low_forecast = str(round(float(high_forecast) - 1, 1))
        
        # weather_string = weatherDay + " " + high_forecast + " " + low_forecast + " " + rain_forecast

        weather_string = weatherDay + " " + srad + " " + high + " " + low + " " + rain
        
        forecast_text.append(weather_string)

    return forecast_text

def forecastData(previousArray):
    mean = np.mean(previousArray)
    std = np.std(previousArray)
    value = np.random.normal(mean, std/2, 1)
    return(value[0])

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