
import numpy as np
import pandas as pd
import os
import watchtower, logging

environment = os.environ['ENV']


if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

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

def altForecastWeather(weather_text):

    fileFluff = ""
    tempDay = 1
    numDivisions = 6

    monthlyData = []

    for index, endPoint in enumerate(monthRanges):
        monthlyItems = []
        for line in weather_text:
            items = line.split(" ")
            items = [x for x in items if x]

            if len(items) == 0 or not items[0].isdigit():
                if index == 0:
                    fileFluff += line + "\n"
                continue
            
            else:
                day = int(items[0][4:])
                if day < tempDay:
                    continue
                elif day >= endPoint - 1:
                    tempDay = day
                    break
                else:
                    monthlyItems.append(items)
        monthlyData.append(monthlyItems)

    monthlyForecast = ""
    for month in monthlyData:
        maxTemp = float(month[0][2])
        minTemp = float(month[0][3])
        for day in month:
            highTemp = float(day[2])
            if highTemp > maxTemp:
                maxTemp = highTemp
            lowTemp = float(day[3])
            if lowTemp < minTemp:
                minTemp = lowTemp

        tempRange = maxTemp - minTemp
        divider = tempRange/numDivisions
        
        tempRanges = [round(minTemp + (divider * (div+1)), 1) for div in range(numDivisions)]

        for day in month:
            highTemp = float(day[2])
            lowTemp = float(day[3])

            for index, highBound in enumerate(tempRanges):
                lowBound = tempRanges[index-1] if index > 0 else minTemp
                if (highTemp <= highBound and highTemp >= lowBound) or index == len(tempRanges)-1:
                    randHighTemp = round(np.random.uniform(lowBound, highBound), 1)
                    break
                if (lowTemp <= highBound and lowTemp >= lowBound):
                    randLowTemp = round(np.random.uniform(lowBound, highBound), 1)

            forecastString = f"{day[0]:<7}{day[1]:>6}{float(randHighTemp):>6}{randLowTemp:>6}{day[4]:>6}{day[5]:>6}{day[6]:>6}"
            monthlyForecast += forecastString

    return monthlyForecast

def yearlyRandomizer():

    if environment == 'prod':
        logger.info(os.path)
        logger.info(os.getcwd())
        logger.info(os.listdir(os.getcwd()))

    fileNames = ['NEME0401', 'NEME0501', 'NEME0601', 'NEME0701', 'NEME0801', 'NEME0901', 'NEME1001', 'NEME1101', 'NEME1201', 'NEME1301', 'NEME1401', 'NEME1501', 'NEME1601', 'NEME1701', 'NEME1801', 'NEME1901', 'NEME2001', 'NEME2101', 'NEME2201', 'NEME2301']

    newWeather = ""
    tempDay = 1

    try:
        for index, endPoint in enumerate(monthRanges):
            randomYear = np.random.choice(fileNames)

            try:
                fileName = f'../weather_files/{randomYear}.WTH'
            except:
                fileName = "NEME2001.WTH"
                logger.info("USING BACKUP WEATHER FILE")

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

    except Exception as e:
        logger.info("YEARLYRANDOMIZER ERROR:", e)

    file = open("NEME0000.WTH", "w")
    file.write(newWeather)
    file.close()

    return