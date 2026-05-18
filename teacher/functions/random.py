import os
import watchtower, logging
import numpy as np
import random

environment = os.environ['ENV']


if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

monthRanges = [32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 367]

def yearlyRandomizer():

    fileNames = ['NEME0401', 'NEME0501', 'NEME0601', 'NEME0701', 'NEME0801', 'NEME0901', 'NEME1001', 'NEME1101', 'NEME1201', 'NEME1301', 'NEME1401', 'NEME1501', 'NEME1601', 'NEME1701', 'NEME1801', 'NEME1901', 'NEME2001', 'NEME2101', 'NEME2201', 'NEME2301']

    newWeather = ""
    tempDay = 1

    for index, endPoint in enumerate(monthRanges):
        randomYear = np.random.choice(fileNames)

        try:
            fileName = f'weather_files/{randomYear}.WTH'
            file = open(fileName, 'r')
            text = file.readlines()
            file.close()
        except:
            fileName = "NEME2001.WTH"
            file = open(fileName, 'r')
            text = file.readlines()
            file.close()
            if environment == 'prod':
                logger.info("USING BACKUP FILE")

        for line in text:
            items = line.split(" ")
            if len(items) > 0 and items[0].isdigit():
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

def monthlyFabricator(weather_text):


    tempDay = 1
    numDivisions = 6

    preamble = ""
    monthlyData = []

    for index, endPoint in enumerate(monthRanges):
        monthlyItems = []
        for line in weather_text.split("\n"):
            items = line.split(" ")
            items = [x for x in items if x]

            if len(items) == 0 or not items[0].isdigit():
                if index == 0:
                    preamble += line + "\n"
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
        maxRain = float(month[0][4])
        for day in month:
            highTemp = float(day[2])
            if highTemp > maxTemp:
                maxTemp = highTemp
            lowTemp = float(day[3])
            if lowTemp < minTemp:
                minTemp = lowTemp
            rain = float(day[4])
            if maxRain < rain:
                maxRain = rain

        tempRange = maxTemp - minTemp
        tempDivider = tempRange/numDivisions

        rainDivider = maxRain/numDivisions
        
        tempRanges = [round(minTemp + (tempDivider * (div+1)), 1) for div in range(numDivisions)]
        rainRanges = [round(rainDivider * (div+1), 1) for div in range(numDivisions)]

        for day in month:
            highTemp = float(day[2])
            lowTemp = float(day[3])
            rain = float(day[4])

    
            for index, highBound in enumerate(tempRanges):
                lowBound = tempRanges[index-1] if index > 0 else minTemp
                if (lowTemp <= highBound and lowTemp >= lowBound):
                    randLowTemp = round(np.random.uniform(lowBound, highBound), 1)
                if (highTemp <= highBound and highTemp >= lowBound) or index == len(tempRanges)-1:
                    randHighTemp = round(np.random.uniform(lowBound, highBound), 1)
                    break

            randRain = 0
            for index, highBound in enumerate(rainRanges):
                lowBound = rainRanges[index-1] if index > 0 else 0
                if (rain <= highBound and rain >= lowBound):
                    randRain = round(np.random.uniform(lowBound, highBound), 1)


            forecastString = f"{day[0]:<7}{day[1]:>6}{str(randHighTemp):>6}{str(randLowTemp):>6}{str(randRain):>6}{day[5]:>6}{day[6]:>6}\n"
            monthlyForecast += forecastString
        
    return "".join([preamble, monthlyForecast])



def forecastWeather(weather_text, forecasting=True):  

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
            
        high_forecast = str(round(forecastTemp(high), 1)) if forecasting else str(round(high, 1))
        low_forecast = str(round(forecastTemp(low), 1 )) if forecasting else str(round(low, 1))
        rain_forecast = str(abs(round(forecastRain(rain), 2))) if forecasting else str(round(rain, 2))

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
    return "".join(newText)