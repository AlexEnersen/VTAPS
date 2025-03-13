#!/usr/local/bin/python3

from django.shortcuts import render, redirect
import os
import time
from singleplayer.forms import IrrigationEntriesForm, FertilizerEntriesForm, SingleplayerProfileForm, FertilizerInitForm
from .models import SingleplayerProfile, FertilizerInit
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')
from io import StringIO
import statistics
import shutil
import zipfile
import boto3
from django.contrib.sessions.models import Session
import environ
import sys
import math
import watchtower, logging

from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt

environment = os.environ['ENV']


if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

def startGame(request):

    user = SingleplayerProfile()
    user.save()
    request.session['user_id'] = user.id
    return render(request, "singleplayer/home.html", {})

@ensure_csrf_cookie
@csrf_protect
def pickHybrid(request):
    context = {}
    hybrid_form = SingleplayerProfileForm()
    fert_form = FertilizerInitForm()

    if hybrid_form.is_valid():
        hybrid_form.save()

    context['hybrid_form'] = hybrid_form
    context['fert_form'] = fert_form

    return render(request, "singleplayer/hybrid.html", context)

@ensure_csrf_cookie
@csrf_protect
def weeklySelection(request):
    context = {}
    matplotlib.pyplot.close()

    user_id = request.session.get('user_id', None) 
    user = SingleplayerProfile.objects.get(id=user_id)
    if (user.week >= 24):
        return redirect("/singleplayer/final")
    
    controlFile = 'UNLI2201.MZX'
    try:
        file = open(controlFile, 'r')
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

    if not os.path.exists("id-%s" % user_id):
        createDirectory(user_id)

    if environment == 'prod':
        logger.info(os.path)
        logger.info(os.getcwd())
        logger.info(os.listdir(os.getcwd()))
    
    if not os.getcwd().split("/")[-1] == "id-%s" % user_id:
        os.chdir("id-%s" % user_id)

        
    if environment == 'prod':
        logger.info(os.path)
        logger.info(os.getcwd())
        logger.info(os.listdir(os.getcwd()))

    if (request.POST.get('hybrid') != None):
        request.session['start_date'] = start_date
        user.hybrid = request.POST['hybrid']
        user.seeding_rate = request.POST['seeding_rate']
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
            file = open(controlFile, 'r')
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
        text = addIrrigation(text, irrigationQuantity, int(date)-7)

        newText = "".join(text)
        try:
            file2 = open(controlFile, 'w')
            file2.write(newText)
            file2.close()
        except Exception as error:
            if environment == 'prod':
                logger.info('error:', error)
            else:
                print("error:", error)

        computeDSSAT(user_id, user.hybrid, controlFile)

    context['week'] = user.week

    iform = IrrigationEntriesForm()
    if iform.is_valid():
        iform.save()
    context['iform'] = iform

    fert_init = FertilizerInit.objects.get(id=user.fert_id)
    fert_entry = fert_init.week1 if user.week == 1 else fert_init.week6 if user.week == 6 else fert_init.week9 if user.week == 9 else fert_init.week10 if user.week == 10 else fert_init.week12 if user.week == 12 else fert_init.week14 if user.week == 14 else fert_init.week15 if user.week == 15 else 0
    context['fert_entry'] = fert_entry
    
    fform = FertilizerEntriesForm(initial = {'fertilizer': fert_entry})
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
    context['other_costs'] = round(11.68 + 11 + 120.4, 2)
        
    if (user.week > 1):
        context['aquaspy_graph'] = plotAquaSpy(date, start_day)
        context['root_depth_graph'] = plotOneAttribute(date, start_day, 'UNLI2201.OPG', 'RDPD', 'cm', 'Root Depth')
        context['water_layer_graph'] = plotWaterLayers(date, start_day)

    matplotlib.pyplot.close()

    
    if os.getcwd().split("/")[-1] == "id-%s" % user_id:
        os.chdir("..")
    
    return render(request, "singleplayer/weekly.html", context)

def finalResults(request):
    context = {}

    start_date = int(request.session.get('start_date', None))
    start_date_str = str(start_date)
    start_day = int(start_date_str[len(start_date_str) - 3:])

    user_id = request.session.get('user_id', None) 
    user = SingleplayerProfile.objects.get(id=user_id)
    date = str(start_date + (user.week * 7))

    if not os.getcwd().split("/")[-1] == "id-%s" % user_id:
        os.chdir("id-%s" % user_id)

    if os.getcwd().split("/")[-1] == "id-%s" % user_id:
        os.chdir("..")

    request.session.clear()

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
    tuesday = request.POST.get('tuesday')
    wednesday = request.POST.get('wednesday')
    thursday = request.POST.get('thursday')
    friday = request.POST.get('friday')
    saturday = request.POST.get('saturday')
    sunday = request.POST.get('sunday')

    return [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
        
def addIrrigation(text, irrigationQuantity, date):
    onIrrigation = False
    dateOffset = 0

    irrigationLines = []

    for quantity in irrigationQuantity:
        if float(quantity) > 0:
            quantity = inchesToMM(float(quantity))
            beforeSpaces = " " * (6 - len(quantity))
            newString = " 1 %s IR001%s%s\n" % (date+dateOffset, beforeSpaces, quantity)
            irrigationLines.append(newString)
        dateOffset += 1

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

    lowArray = []
    highArray = []
    rainArray = []

    try:
        weather_file = open("NENP2201.WTH", 'r')
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
        forecast_file = open("forecast.txt", 'w')
    except Exception as error:
        if environment == 'prod':
            logger.info('error', error)
        else:
            print("compileWeather error:", error)

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

        forecast_file.write(weather_string)

    forecast_file.close()

        
def getWeather(date):
    lowArray = []
    highArray = []
    dateFound = False
    weatherInfo = []

    day = date[len(date) - 3:]

    if environment == 'prod':
        logger.info(os.path.dirname(os.path.realpath(__file__)))
        logger.info(os.listdir(os.path.dirname(os.path.realpath(__file__))))

    try:
        file = open("forecast.txt", 'r')
        text = file.readlines()
        file.close()

        for line in text:
            items = list(filter(None, line.split(" ")))
            weatherDay = items[0]

            # converted_day = datetime.strptime("2022-" + day, "%Y-%j").strftime("%m-%d-%Y")

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
                
                weatherData = {"day": weatherDateConversion, "tHigh": items[1], "tLow": items[2], "pRain": mmToInches(float(items[3]))}

                weatherInfo.append(weatherData)

                if int(weatherDay) - int(day) >= 6:
                    dateFound = False
                    return weatherInfo
    
    except Exception as error:
        if environment == 'prod':
            logger.info(error)
        else:
            print("getWeather error:", error)

def forecastData(previousArray):
    mean = np.mean(previousArray)
    std = np.std(previousArray)
    value = np.random.normal(mean, std/2, 1)
    return(value[0])

def mmToInches(mm):
    inches = round(float(0.0393701 * mm), 1)
    return inches

def inchesToMM(inches):
    mm = round(float(25.4 * inches), 1)
    return str(mm)

def plotOneAttribute(date, start_day, filename, attribute, yaxis, title):

    try:
        file = open(filename, 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    day = int(date[len(date) - 3:])
    
    readingStress = False

    waterStress_Days = []
    waterStress_Values = []
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
            waterStress_Days.append(int(adjusted_day))
            waterStress_Values.append(float(items[index]))

    #REFERENCE FOR CODE TO DISPLAY GRAPH IN TEMPLATE: https://stackoverflow.com/questions/40534715/how-to-embed-matplotlib-graph-in-django-webpage
    fig, ax = plt.subplots()
    ax.plot(waterStress_Values)
    # ax.legend(loc='upper left')
    ax.set_xlabel('Days since planting')
    ax.set_ylabel(yaxis)
    fig.suptitle(title, fontsize=16)
    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    plt.close()
    
    return data

def plotAquaSpy(date, start_day):
    day = int(date[len(date) - 3:])
    try:
        file = open("NE.SOL", 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    rootArray = getRootDepth(date)

    readingSoil = False
    index = -1
    soilArray = []

    for line in text:
        items = list(filter(None, line.strip("\n").split(" ")))
        if len(items) == 0 and not readingSoil:
            continue
        elif len(items) > 0 and not readingSoil:
            if (items[0] == "@" and items[1] == "SLB"):
                index = items.index("SDUL") - 1
                index2 = items.index("SLLL") - 1
                readingSoil = True
        elif len(items) > 1 and readingSoil:
            soilArray.append({'upperLimit': float(items[index]), 'lowerLimit': float(items[index2]), "depth": int(items[0])})
            if int(items[0]) > rootArray[-1]:
                break
    try:
        file2 = open("UNLI2201.OSW", "r")
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
                modifier = 12
                for index, soilLayer in enumerate(soilArray):
                    waterLayer = float(items[index2 + index])
                    soilDepth = soilLayer['depth'] - depthTracker
                    rootDepth = rootArray[rootDay] - depthTracker
                    if rootDepth < soilDepth:
                        currentArray.append(round(waterLayer * (rootDepth / soilDepth), 3))
                        ulimitTempArray.append(round(soilLayer['upperLimit'] * (rootDepth / soilDepth), 3))
                        llimitTempArray.append(round(soilLayer['lowerLimit'] * (rootDepth / soilDepth), 3))
                        break
                    else:
                        currentArray.append(round(waterLayer, 3))
                        ulimitTempArray.append(round(soilLayer["upperLimit"], 3))
                        llimitTempArray.append(round(soilLayer["lowerLimit"], 3))
                    depthTracker += soilDepth
                rootDay += 1
                waterArray.append(round(sum(currentArray), 3) * modifier)
                ulimitArray.append(round(sum(ulimitTempArray), 3) * modifier)
                llimitArray.append(round(sum(llimitTempArray), 3) * modifier)

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
        file = open("UNLI2201.OSW", 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

    readingWater = False
    layerNum = 13
    waterLayers = [[] for i in range(layerNum)]
    soilVolumes = []

    for textIndex, line in enumerate(text):
        items = list(filter(None, line.strip("\n").split(" ")))
        if len(items) == 0 and not readingWater:
            continue
        elif len(items) > 0 and not readingWater:
            if (items[0] == "!" and items[1].startswith("0-")):
                soilVolumes = [item for item in items]
                soilVolumes.pop(0)
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
                    layer.append(float(items[index+index2]) + (layerNum - index2))

    fig, ax = plt.subplots()
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.75, box.height])           
    plt.plot(waterLayers[0])
    plt.plot(waterLayers[1])
    plt.plot(waterLayers[2])
    plt.plot(waterLayers[3])
    plt.plot(waterLayers[4])
    plt.plot(waterLayers[5])
    plt.plot(waterLayers[6])
    plt.plot(waterLayers[7])
    plt.plot(waterLayers[8])
    plt.plot(waterLayers[9])
    plt.plot(waterLayers[10])
    plt.plot(waterLayers[11])
    plt.plot(waterLayers[12])
    plt.xlabel('Days since planting')
    plt.ylabel("Soil Water Amount")
    plt.yticks([])
    plt.legend(soilVolumes, loc="upper right", bbox_to_anchor = (1.35, 1))
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
        file = open("UNLI2201.OPG", 'r')
        text = file.readlines()
        file.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)

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
            rootArray.append(float(items[33]) * 100)
            if int(items[1]) == day:
                return rootArray
        
    return rootArray
        
# def getEconomics(date):
#     file = open("UNLI2201.MZX")
#     text = file.readlines()
#     file.close()
#     print(date)

#     day = int(date[len(date) - 3:])
#     readingWater = False
#     readingFert = False
    
#     waterTotal = 0
#     fertTotal = 0

#     for line in text:
#         items = list(filter(None, line.strip("\n").split(" ")))
#         if len(items) > 0 and items[0] == "@I" and items[3] == "IRVAL":
#             readingWater = True
#             readingFert = False
#         elif len(items) > 0 and items[0] == "@F":
#             readingFert = True
#             readingWater = False
#         elif readingWater:
#             if len(items) > 0 and int(items[1]) <= int(date):
#                 waterTotal += float(items[3])
#             else:
#                 readingWater = False
#         elif readingFert:
#             if len(items) > 0 and int(items[1]) <= int(date):
#                 fertTotal += float(items[5])
#             else:
#                 readingFert = False

#     return [waterTotal, fertTotal]

def computeDSSAT(user_id, hybrid, controlFile):
    try:
        commandFile = open("command.ps1", "w")
        commandFile.write("../../DSCSM048 %s A %s" % (hybrid, controlFile))
        commandFile.close()
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("error:", error)
            
    zip = zipfile.ZipFile("id-%s.zip" % (user_id), "w", zipfile.ZIP_DEFLATED)
    zip.write("command.ps1")
    zip.write("NE.SOL")
    zip.write("NENP2201.WTH")
    zip.write("UNLI2201.MZX")
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
        
        s3.upload_file("id-%s.zip" % (user_id), "vtapsbucket", "id-%s.zip" % (user_id))


        os.remove("id-%s.zip" % (user_id))
        os.remove("command.ps1")


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

        s3.download_file('outputvtapsbucket', "id-%s/id-%s.zip" % (user_id, user_id), "id-%s.zip" % user_id)

        s3.delete_object(Bucket='outputvtapsbucket', Key='id-%s/id-%s.zip' % (user_id, user_id))

        zip = zipfile.ZipFile("id-%s.zip" % user_id, 'r')
        zip.extractall(".")
        zip.close()

        files = os.listdir(".")
        for file in files:
            if file.startswith("id-%s\\" % user_id):
                os.rename(file,file.split("\\")[1])

        os.remove("id-%s.zip" % user_id)
    except Exception as error:
        if environment == 'prod':
            logger.info('error:', error)
        else:
            print("Error:", error)

def createDirectory(user_id):
    if not os.path.isdir("id-%s" % (user_id)):
        os.mkdir("id-%s" % (user_id))
        shutil.copy2("UNLI2201.MZX", "id-%s/" % (user_id))
        shutil.copy2("NE.SOL", "id-%s/" % (user_id))
        shutil.copy2("NENP2201.WTH", "id-%s/" % (user_id))

