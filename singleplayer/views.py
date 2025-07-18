#!/usr/local/bin/python3

from django.shortcuts import render, redirect
import os
import time
from singleplayer.forms import IrrigationEntriesForm, FertilizerEntriesForm1, FertilizerEntriesForm2, SingleplayerProfileForm, FertilizerInitForm
from .models import SingleplayerProfile, FertilizerInit
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')
from io import StringIO
import shutil
import zipfile
import boto3
import environ
import watchtower, logging
from .functions.functions import *
from .functions.fileSearch import *
from django.contrib.auth import get_user_model
import pandas as pd

environment = os.environ['ENV']

userPath = ""

if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

def startGame(request):

    user = SingleplayerProfile()
    user.save()
    request.session['user_id'] = user.id
    return render(request, "singleplayer/intro.html", {})

def pickHybrid(request):
    context = {}
    hybrid_form = SingleplayerProfileForm()
    fert_form = FertilizerInitForm()

    if hybrid_form.is_valid():
        hybrid_form.save()

    context['hybrid_form'] = hybrid_form
    context['fert_form'] = fert_form

    return render(request, "singleplayer/hybrid.html", context)

def weeklySelection(request):
    context = {}
    matplotlib.pyplot.close()

    user_id = request.session.get('user_id', None) 
    user = SingleplayerProfile.objects.get(id=user_id)
    
    global userPath
    userPath = f"id-{user_id}/"

    if not os.path.exists(userPath):
        createDirectory(userPath)
    
    controlFile = 'UNLI2309.MZX'
    try:
        file = open(userPath + controlFile, 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    start_date = str(int(getDate(text)))
    date = str(int(start_date) + (((user.week)-1) * 7))

    context = {}
    fert_entry = -1

        
    if environment == 'prod':
        logger.info(os.path)
        logger.info(os.getcwd())
        logger.info(os.listdir(os.getcwd()))

    if (request.POST.get('hybrid') != None):
        request.session['start_date'] = start_date
        user.hybrid = request.POST['hybrid']
        user.seeding_rate = request.POST['seeding_rate']
        text = setSeedingRate(text, user.seeding_rate)
        user.week = 1
        user.weather_type = request.POST['weather_type']

        fertilizer_init = FertilizerInit(week1 = request.POST['week1'], week6 = request.POST['week6'], week9 = request.POST['week9'], week10 = request.POST['week10'], week12 = request.POST['week12'], week14 = request.POST['week14'], week15 = request.POST['week15'])
        fertilizer_init.save()
        user.fert_id = fertilizer_init.id

        user.save()

        compileWeather()

    elif len(request.POST.keys()) > 0:

        user.week += 1
        user.save()

        date = str(int(start_date) + (((user.week)-1) * 7))
        try:
            file = open(userPath + controlFile, 'r')
            text = file.readlines()
            file.close()
        except Exception as error:
            if environment == 'prod':
                logger.info('error:', error)
            else:
                print("error:", error)

        fertilizerQuantity = request.POST.get('fertilizer')
        irrigationQuantity = getIrrigation(request)
        
        text = addFertilizer(text, fertilizerQuantity, int(date)-7)
        text = addIrrigation(text, irrigationQuantity, fertilizerQuantity, int(date)-7)

        computeDSSAT(user_id, user.hybrid, controlFile)

    newText = "".join(text)
    try:
        file2 = open(userPath + controlFile, 'w')
        file2.write(newText)
        file2.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    context['week'] = user.week

    iform = IrrigationEntriesForm()
    if iform.is_valid():
        iform.save()
    context['iform'] = iform

    fert_init = FertilizerInit.objects.get(id=user.fert_id)
    fert_entry = fert_init.week1 if user.week == 1 else fert_init.week6 if user.week == 6 else fert_init.week9 if user.week == 9 else fert_init.week10 if user.week == 10 else fert_init.week12 if user.week == 12 else fert_init.week14 if user.week == 14 else fert_init.week15 if user.week == 15 else 0
    context['fert_entry'] = fert_entry
    
    fform = FertilizerEntriesForm1(initial = {'fertilizer': fert_entry}) if user.week <= 6 else FertilizerEntriesForm2(initial = {'fertilizer': fert_entry})
    if fform.is_valid():
        fform.save()

    context['fform'] = fform

    context['weather'] = getWeather(date)

    start_date_str = str(start_date)

    start_day = int(start_date_str[len(start_date_str) - 3:])

    total_irrigation_cost = getTotalIrrigationCost(text, date)
    total_fertilizer_cost = getTotalFertilizerCost(text, date)

    context['irr_cost'] = round(total_irrigation_cost, 2)
    context['fert_cost'] = round(total_fertilizer_cost, 2)

    # Insurance + Insecticide + Seeds
    context['other_costs'] = round(142.79, 2)

    context['total_cost'] = round(context['irr_cost'] + context['fert_cost'] + context['other_costs'], 2)
    context['bushel_cost'] = round(context['total_cost']/230, 2)
        
    if (user.week > 1):
        context['aquaspy_graph'] = plotAquaSpy(date, start_day)
        context['root_depth_graph'] = plotOneAttribute(date, start_day, 'UNLI2309.OPG', 'RDPD', 'Inches (in)', 'Root Depth')
        context['growth_stage_graph'] = plotOneAttribute(date, start_day, 'UNLI2309.OPG', 'GSTD', 'Stage', 'Growth Stage')
        context['nitrogen_stress_graph'] = plotOneAttribute(date, start_day, 'UNLI2309.OPG', 'NSTD', 'N Stress', 'Nitrogen Stress')
        context['water_layer_graph'] = plotWaterLayers(date, start_day)
        context['weather_history'] = getWeatherHistory(date, start_day)

    matplotlib.pyplot.close()
    
    
    if (user.week >= 24):
        return redirect("/singleplayer/final")
    else:
        return render(request, "singleplayer/weekly.html", context)

def finalResults(request):
    
    user_id = request.session.get('user_id', None) 
    user = SingleplayerProfile.objects.get(id=user_id)

    context = {}

    controlFile = 'UNLI2309.MZX'
    try:
        file = open(userPath + controlFile, 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    start_date = int(request.session.get('start_date', None))
    start_day = int(str(start_date)[len(str(start_date)) - 3:])
    date = str(start_date + (user.week * 7))

    total_irrigation_cost = round(getTotalIrrigationCost(text, date), 2)
    total_fertilizer_cost = round(getTotalFertilizerCost(text, date), 2)

    context['irr_cost'] = total_irrigation_cost
    context['fert_cost'] = total_fertilizer_cost

    # Insurance + Insecticide + Seeds
    context['other_costs'] = round(142.79, 2)
    context['total_cost'] = round(total_irrigation_cost + total_fertilizer_cost + context['other_costs'], 2)

    finalYield = getFinalYield()

    context['bushel_cost'] = round(context['total_cost']/finalYield, 2)
    context['yield'] = finalYield

    
    context['aquaspy_graph'] = plotAquaSpy(date, start_day)
    context['water_layer_graph'] = plotWaterLayers(date, start_day)

    # request.session.clear()

    return render(request, "singleplayer/final.html", context)
    
def getDate(text):
    onDate = False
    for line in text:
        if (line.startswith("@P PDATE")):
            onDate = True
        elif (onDate):
            onDate = False
            lineItems = line.split()
            return lineItems[1]
        
def getIrrigation(request):
    monday = request.POST.get('monday')
    thursday = request.POST.get('thursday')

    return [monday, thursday]
        
def addIrrigation(text, irrigationQuantity, fertilizerQuantity, date):
    onIrrigation = False

    irrigationLines = []

    for index, quantity in enumerate(irrigationQuantity):
        quantity = float(quantity)
        if index == 0:
            quantity += (float(fertilizerQuantity if fertilizerQuantity else 0) * 0.01)
        if quantity > 0:
            quantity = inchesToMM(quantity)
            beforeSpaces = " " * (6 - len(quantity))
            if index == 0:
                newString = " 1 %s IR001%s%s\n" % (date, beforeSpaces, quantity)
            elif index == 1:
                newString = " 1 %s IR001%s%s\n" % (date+3, beforeSpaces, quantity)
            irrigationLines.append(newString)

    for i, line in enumerate(text):
        if (line.startswith("@I")):
            onIrrigation = True
        

        if (onIrrigation and line == "\n"):
            for j, line in enumerate(irrigationLines):
                text.insert(i+j, line)
            return text

def getTotalIrrigationCost(text, date):
    onIrrigation = False
    totalIrrigationCost = 0

    for i, line in enumerate(text):
        lines = list(filter(None, line.strip("\n").split(" ")))
        if (len(lines) < 4):
            if (onIrrigation):
                break
            else:
                continue

        if (onIrrigation):
            if (lines[0].startswith("*") or lines[0].startswith("@")):
                break
            elif (int(lines[1]) < int(date)):
                totalIrrigationCost += mmToInches(float(lines[3])) * 6.1
            else:
                break

        if (lines[3] == "IRVAL"):
            onIrrigation = True

    return totalIrrigationCost

        
def addFertilizer(text, fertilizerQuantity, date):

    if fertilizerQuantity == None or int(fertilizerQuantity) == 0:
        return text

    onFertilizer = False

    beforeSpaces = " " * (6-len(fertilizerQuantity))


    for i, line in enumerate(text):
        if (line.startswith("@F")):
            onFertilizer = True
        
        if (onFertilizer and line == "\n"):
            newString = " 1 %s FE001 AP001    10%s%s   -99   -99   -99   -99   -99 -99\n" % (str(date), beforeSpaces, fertilizerQuantity)
            text.insert(i, newString)
            onFertilizer = False
            return text
    

def getTotalFertilizerCost(text, date):
    onFertilizer = False
    totalFertilizerCost = 0
    startIndex = -1

    for i, line in enumerate(text):
        lines = list(filter(None, line.strip("\n").split(" ")))
        if (len(lines) < 6):
            if (onFertilizer):
                break
            else:
                continue

        elif (onFertilizer):
            if (lines[0].startswith("*") or lines[0].startswith("@")):
                break
            elif (int(lines[1]) < int(date)):
                if float(lines[5]) == 0:
                    startIndex += 1
                    continue
                if (i - startIndex < 3):
                    totalFertilizerCost += (float(lines[5]) * 0.6) + 8.50
                else:
                    totalFertilizerCost += (float(lines[5]) * 0.6) + 1.25
            else:
                break

        elif (lines[5] == "FAMN"):
            onFertilizer = True
            startIndex = i

    return totalFertilizerCost
        
def compileWeather():

    altForecast = True
    filename = "NEME0000.WTH"

    if altForecast:
        yearlyRandomizer(userPath)

    try:
        weather_file = open(userPath + filename, 'r')
        weather_text = weather_file.readlines()
        weather_file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error', error)
        else:
            print("error:", error)

    if environment == 'prod':
        logger.info(os.path.dirname(os.path.realpath(__file__)))
        logger.info(os.listdir(os.path.dirname(os.path.realpath(__file__))))

    try:
        forecast_file = open(userPath + "forecast.txt", 'w')
    except Exception as error:
        if environment == 'prod':
            logger.info('error', error)
        else:
            print("compileWeather error:", error)
    
    forecast_text = altForecastWeather(weather_text) if altForecast else forecastWeather(weather_text)

    forecast_file.write(forecast_text)

    forecast_file.close()

        
def getWeather(date):
    lowArray = []
    highArray = []
    dateFound = False
    weatherInfo = []

    day = date[len(date) - 3:]

    try:
        file = open(userPath + "forecast.txt", 'r')
        text = file.readlines()
        file.close()

        for line in text:
            items = list(filter(None, line.split(" ")))
            items = [x for x in items if x]
            
            weatherDay = items[0][len(items[0]) - 3:]

            if int(day) - int(weatherDay) <= 20 and len(lowArray) < 20:
                highArray.append(float(items[2]))
                lowArray.append(float(items[3]))

            if weatherDay == day:
                dateFound = True

            if dateFound:
                weatherDateConversion = datetime.strptime("2022-" + weatherDay, "%Y-%j").strftime("%m-%d-%Y")
                if (int(weatherDay) - int(day)) == 0:
                    weatherDateConversion = "Monday: " + weatherDateConversion
                elif (int(weatherDay) - int(day)) == 1:
                    weatherDateConversion = "Tuesday: " + weatherDateConversion
                elif (int(weatherDay) - int(day)) == 2:
                    weatherDateConversion = "Wednesday: " + weatherDateConversion
                elif (int(weatherDay) - int(day)) == 3:
                    weatherDateConversion = "Thursday: " + weatherDateConversion
                elif (int(weatherDay) - int(day)) == 4:
                    weatherDateConversion = "Friday: " + weatherDateConversion
                elif (int(weatherDay) - int(day)) == 5:
                    weatherDateConversion = "Saturday: " + weatherDateConversion
                elif (int(weatherDay) - int(day)) == 6:
                    weatherDateConversion = "Sunday: " + weatherDateConversion
                
                weatherData = {"day": weatherDateConversion, "tHigh": round(float(items[2]) * (9/5) + 32, 1), "tLow": round(float(items[3]) * (9/5) + 32, 1), "pRain": mmToInches(float(items[3]))}

                weatherInfo.append(weatherData)

                if int(weatherDay) - int(day) >= 6:
                    dateFound = False
                    return weatherInfo
    
    except Exception as error:
        if environment == 'prod':
            logger.info(error)
        else:
            print("getWeather error:", error)

def mmToInches(mm):
    inches = round(float(0.0393701 * mm), 1)
    return inches

def inchesToMM(inches):
    mm = round(float(25.4 * inches), 1)
    return str(mm)

def plotOneAttribute(date, start_day, filename, attribute, yaxis, title):

    try:
        file = open(userPath + filename, 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)
        return None

    day = int(date[len(date) - 3:])
    
    readingStress = False

    days = []
    attribute_values = []
    index = -1

    for line in text:
        items = list(filter(None, line.split(" ")))
        if len(items) <= 3 and not readingStress:
            continue
        elif (readingStress and len(items) == 0) or (readingStress and int(items[1]) > day):
            break
        elif len(items) > 3 and not readingStress:
            if (items[0] == "@YEAR"):
                index = items.index(attribute)
                readingStress = True
        elif len(items) > 1 and readingStress and index > -1 and int(items[1]) >= int(start_day):
            adjusted_day = int(items[1]) - start_day
            days.append(int(adjusted_day))
            if attribute == "RDPD":
                attribute_values.append(float(items[index]) / 2.54 * 100)
            else:
                attribute_values.append(float(items[index]))

    #REFERENCE FOR CODE TO DISPLAY GRAPH IN TEMPLATE: https://stackoverflow.com/questions/40534715/how-to-embed-matplotlib-graph-in-django-webpage
    fig, ax = plt.subplots()
    ax.plot(attribute_values)
    # ax.legend(loc='upper left')
    ax.set_xlabel('Days since planting')
    ax.set_ylabel(yaxis)
    if attribute == 'RDPD':
        ax.invert_yaxis()
    fig.suptitle(title, fontsize=16)
    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    plt.close()
    
    return data

def getFinalYield():
    filename = 'UNLI2309.OOV'
    try:
        file = open(userPath + filename, 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)
        return None
    
    readingVariables = False
    finalYield = -1

    for line in text:
        items = list(filter(None, line.split(" ")))
        if items[0] == '@' and not readingVariables:
            readingVariables = True
        elif readingVariables and items[0].startswith('Yield'):
            finalYield = round(float(items[-2]) / 62.77, 1)
            return finalYield

def plotAquaSpy(date, start_day):
    day = int(date[len(date) - 3:])
    try:
        file = open(userPath + "NE.SOL", 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    rootArray = getRootDepth(date)
    if not rootArray:
        return None

    readingSoil = False
    readingFile = False
    index = -1
    soilArray = []

    for line in text:
        items = list(filter(None, line.strip("\n").split(" ")))
        if len(items) == 0 and not readingSoil:
            continue
        elif len(items) > 0 and not readingSoil:
            if (items[0] == '*NENP230018'):
                readingFile = True
                continue
            elif (readingFile and items[0] == "@" and items[1] == "SLB"):
                index = items.index("SDUL") - 1
                index2 = items.index("SLLL") - 1
                readingSoil = True
        elif len(items) > 1 and readingSoil:
            soilArray.append({'upperLimit': float(items[index]), 'lowerLimit': float(items[index2]), "depth": int(items[0])})
            if int(items[0]) > rootArray[-1]:
                break
    try:
        file2 = open(userPath + "UNLI2309.OSW", "r")
        text2 = file2.readlines()
        file2.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    readingWater = False
    index2 = -1
    waterArray = []
    ulimitArray = []
    llimitArray = []
    rootDay = 0

    for line in text2:
        currentArray = []
        ulimitTempArray = []
        llimitTempArray = []
        items = list(filter(None, line.strip("\n").split(" ")))
        if len(items) == 0 and not readingWater:
            continue
        elif len(items) > 0 and not readingWater:
            if (items[0] == "@YEAR"):
                index2 = items.index("SW1D")
                readingWater = True
        elif len(items) > 1 and readingWater:
            if int(items[1]) < int(start_day):
                continue
            elif int(items[1]) > day:
                break
            else:
                depthTracker = 0
                modifier = 2.5
                for index, soilLayer in enumerate(soilArray):
                    waterLayer = float(items[index2 + index])
                    soilDepth = soilLayer['depth'] - depthTracker
                    rootDepth = rootArray[rootDay] - depthTracker
                    if rootDepth < soilDepth:
                        currentArray.append(round(waterLayer * rootDepth, 3))
                        ulimitTempArray.append(round(soilLayer['upperLimit'] * rootDepth, 3))
                        llimitTempArray.append(round(((soilLayer['upperLimit'] + soilLayer['lowerLimit'])/2) * rootDepth, 3))
                        break
                    else:
                        currentArray.append(round(waterLayer * soilDepth, 3))
                        ulimitTempArray.append(round(soilLayer["upperLimit"] * soilDepth, 3))
                        llimitTempArray.append(round(((soilLayer['upperLimit'] + soilLayer['lowerLimit'])/2) * soilDepth, 3))
                    depthTracker += soilDepth

                rootDay += 1
                waterArray.append(round(sum(currentArray), 3) / modifier)
                ulimitArray.append(round(sum(ulimitTempArray), 3) / modifier)
                llimitArray.append(round(sum(llimitTempArray), 3) / modifier)

    limitRange = range(1, len(ulimitArray)+1)
    waterRange = range(1, len(waterArray)+1)
    
    alpha=0.7

    plt.fill_between(limitRange, ulimitArray, llimitArray, alpha=alpha)
    plt.plot(waterRange, waterArray, color="black")
    plt.xlabel('Days since planting')
    plt.ylabel("Soil Water Limits")
    plt.title("Soil Water", fontsize=16)
    imgdata = StringIO()
    plt.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    plt.close()

    return data

def plotWaterLayers(date, start_day):
    day = int(date[len(date) - 3:])
    try:
        file = open(userPath + "UNLI2309.OSW", 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)
        return None

    readingWater = False
    layerNum = 12
    waterLayers = [[] for i in range(1,layerNum)]
    soilVolumes = []

    for textIndex, line in enumerate(text):
        items = list(filter(None, line.strip("\n").split(" ")))
        if len(items) == 0 and not readingWater:
            continue
        elif len(items) > 0 and not readingWater:
            # if (items[0] == "!" and items[1].startswith("0-")):
            #     soilVolumes = [item for item in items]
            #     soilVolumes.pop(0)
            if (items[0] == "@YEAR"):
                index = items.index("SW1D")
                readingWater = True
        elif len(items) > 1 and readingWater:
            if int(items[1]) < int(start_day):
                continue
            elif int(items[1]) > day:
                break
            else:
                for index2, layer in enumerate(waterLayers):
                    layer.append(float(items[index+index2]) + ((layerNum - index2)/10))

    desiredLayers = waterLayers[1:9]
    legendLayers = ['4"', '8"', '12"', '16"', '24"', '32"', '40"', '48"']

    fig, ax = plt.subplots()
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])
    for layer in desiredLayers:           
        plt.plot(layer)
    plt.xlabel('Days since planting')
    plt.ylabel("Soil Water Amount")
    plt.yticks([])
    plt.legend(legendLayers, loc="upper right", bbox_to_anchor = (1.25, 1))
    # plt.yticks(range(1, layerNum+1), soilVolumes)
    plt.title("Soil Water", fontsize=16)
    imgdata = StringIO()
    plt.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()
    plt.close()

    return data

def getRootDepth(date):
    try:
        file = open(userPath + "UNLI2309.OPG", 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)
        return None

    day = int(date[len(date) - 3:])
    reading = False
    day = 0
    rootArray = []

    for line in text:
        items = list(filter(None, line.split(" ")))
        if len(items) <= 33:
            continue 
        elif not reading and items[0] == "@YEAR":
            reading = True
        elif reading:
            rootArray.append(float(items[33]) * 100 * 0.393701)
            if int(items[1]) == day:
                return rootArray
        
    return rootArray

def getWeatherHistory(date, start_day):
    day = int(date[len(date) - 3:])

    try:
        weatherFile = open(userPath + "NEME0000.WTH", "r")
        weatherText = weatherFile.readlines()
        weatherFile.close()

        forecastFile = open(userPath + "forecast.txt", "r")
        forecastText = forecastFile.readlines()
        forecastFile.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)
        return None
    
    history = []

    forecastIndex = -1
    for line in weatherText:
        items = line.split(" ")
        items = [x for x in items if x]

        if not items[0].isdigit():
            continue
        else:
            forecastIndex += 1

        forecastItems = forecastText[forecastIndex].split(" ")
        forecastItems = [x for x in forecastItems if x]
        tempDay = int(items[0][len(items[0]) - 3:])
        if tempDay < start_day:
            continue
        elif tempDay >= day:
            break
        else:
            weatherDict = {"day": tempDay, "high": round(float(items[2]) * (9/5) + 32, 1), "low": round(float(items[3]) * (9/5) + 32, 1), "rain": items[4], "forecast_high": round(float(forecastItems[2]) * (9/5) + 32, 1), "forecast_low": round(float(forecastItems[3]) * (9/5) + 32, 1), "forecast_rain": forecastItems[4]}
            history.append(weatherDict)
    return history

def computeDSSAT(user_id, hybrid, controlFile):
    try:
        commandFile = open(userPath + "command.ps1", "w")
        commandFile.write("../../DSCSM048 %s A %s" % (hybrid, controlFile))
        commandFile.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    zipFile = f"id-{user_id}.zip"
    zipPath = userPath + zipFile
            
    zip = zipfile.ZipFile(zipPath, "w", zipfile.ZIP_DEFLATED)
    zip.write(userPath + "command.ps1", "command.ps1")
    zip.write(userPath + "NE.SOL", "NE.SOL")
    zip.write(userPath + "NEME0000.WTH", "NEME0000.WTH")
    zip.write(userPath + "UNLI2309.MZX", "UNLI2309.MZX")
    zip.close()

    secret_name = "S3_Keys"
    region_name = "us-east-1"
    
    try:
        if environment == 'prod':
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name
            )

            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
            SECRET_KEY = eval(get_secret_value_response['SecretString'])
            s3 = boto3.client("s3", aws_access_key_id=SECRET_KEY['S3_ACCESS_KEY_ID'], aws_secret_access_key=SECRET_KEY['S3_SECRET_ACCESS_KEY'],)

        else:
            env = environ.Env()
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
            s3 = boto3.client("s3", aws_access_key_id=env('S3_ACCESS_KEY_ID'), aws_secret_access_key=env('S3_SECRET_ACCESS_KEY'),)
        
        s3.upload_file(zipPath, "vtapsbucket", zipFile)


        os.remove(zipPath)
        os.remove(userPath + "command.ps1")


        file_present = False

        bucket = None
        timeout = time.time() + 60*5

        while not file_present:
            try:
                bucket = s3.list_objects_v2(
                    Bucket='outputvtapsbucket',
                    Prefix ='id-%s/' % (user_id),
                    MaxKeys=100 )
            except Exception as error:
                if environment == 'prod':
                    logger.info('error:', error)
                else:
                    print('error:', error)
                
            if time.time() > timeout:
                break
            elif bucket['KeyCount'] > 0:
                file_present = True

        s3.download_file('outputvtapsbucket', zipPath, zipPath)

        s3.delete_object(Bucket='outputvtapsbucket', Key=zipPath)

        zip = zipfile.ZipFile(zipPath, 'r')
        zip.extractall(userPath)
        zip.close()

        files = os.listdir(userPath)
        for file in files:
            if file.startswith("id-%s\\" % user_id):
                os.rename(userPath + file,userPath + file.split("\\")[1])

        os.remove(zipPath)
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("Error:", error)

def createDirectory(userPath):
    if not os.path.isdir(userPath):
        os.mkdir(userPath)
        shutil.copy2("UNLI2309.MZX", userPath)
        shutil.copy2("NE.SOL", userPath)
        shutil.copy2("NEME2001.WTH", userPath)

