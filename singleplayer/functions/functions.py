
import numpy as np
import pandas as pd

monthRanges = [32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366]

def forecastWeather(weather_text):    

    lowArray = []
    highArray = []
    rainArray = []
    forecast_text = ""

    for line in weather_text:
        items = list(filter(None, line.split(" ")))
        weatherDate = items[0]

        if not weatherDate.isnumeric():
            continue
            
        weatherDay = weatherDate[len(weatherDate) - 3:]

        highArray.append(round((float(items[2]) * (9/5)) + 32, 1))
        lowArray.append(round((float(items[3]) * (9/5)) + 32, 1))
        rainArray.append(float(items[4].strip()))

        if len(lowArray) >= 21:
            highArray.pop(0)
            lowArray.pop(0)
            rainArray.pop(0)
            
        high_forecast = str(round(forecastData(highArray), 1))
        low_forecast = str(round(forecastData(lowArray), 1 ))
        rain_forecast = str(abs(round(forecastData(rainArray), 2)))
        
        if high_forecast < low_forecast:
            low_forecast = str(round(float(high_forecast) - 1, 1))
        
        weather_string = weatherDay + " " + high_forecast + " " + low_forecast + " " + rain_forecast + "\n"
        
        forecast_text += weather_string

    return forecast_text



def forecastData(previousArray):
    mean = np.mean(previousArray)
    std = np.std(previousArray)
    value = np.random.normal(mean, std/2, 1)
    return(value[0])

def altForecastWeather():
    
    randomMonthData = yearlyRandomizer().split("\n")

    tempDay = 1
    stratifiedMonthData = ""
    for index, endPoint in enumerate(monthRanges):
        monthlyItems = []
        for line in randomMonthData:
            items = line.split(" ")
            if items[0].isdigit():
                day = int(items[0][4:])
                if day < tempDay:
                    continue
                elif day >= endPoint - 1:
                    tempDay = day
                    break
                else:
                    monthlyItems.append(items)
            else:
                continue

    return ""

def yearlyRandomizer():
    fileNames = ['NEME0401', 'NEME0501', 'NEME0601', 'NEME0701', 'NEME0801', 'NEME0901', 'NEME1001', 'NEME1101', 'NEME1201', 'NEME1301', 'NEME1401', 'NEME1501', 'NEME1601', 'NEME1701', 'NEME1801', 'NEME1901', 'NEME2001', 'NEME2101', 'NEME2201', 'NEME2301']

    newWeather = ""
    tempDay = 1

    for index, endPoint in enumerate(monthRanges):

        randomYear = np.random.choice(fileNames)
        fileName = f'../weather_files/{randomYear}.WTH'

        file = open(fileName, 'r')
        text = file.readlines()
        file.close()

        for line in text:
            items = line.split(" ")
            if items[0].isdigit():
                day = int(items[0][4:])
                if day < tempDay:
                    continue
                elif day >= endPoint - 1:
                    tempDay = day
                    break
                else:
                    newWeather += line
            elif index == 0:
                newWeather += line

    return newWeather