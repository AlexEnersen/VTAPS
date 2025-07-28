#!/usr/local/bin/python3

from django.shortcuts import render, redirect
import os
import time
from game.forms import IrrigationEntriesForm, FertilizerEntriesForm1, FertilizerEntriesForm2, GameProfileForm, FertilizerInitForm
from .models import GameProfile, FertilizerInit
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')
import io
import shutil
import zipfile
import boto3
import environ
import watchtower, logging
from .functions.functions import *
from .functions.fileSearch import *
import pandas as pd

environment = os.environ['ENV']

gamePath = ""
secret_name = "S3_Keys"
region_name = "us-east-1"

if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

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
        s3_access_key = SECRET_KEY['S3_ACCESS_KEY_ID']
        s3_secret_key = SECRET_KEY['S3_SECRET_ACCESS_KEY']
        
    else:
        env = environ.Env()
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
        s3_access_key = env('S3_ACCESS_KEY_ID')
        s3_secret_key = env('S3_SECRET_ACCESS_KEY')

    s3 = boto3.client("s3", aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key)
        
except Exception as error:
    if environment == 'prod':
        logger.info('error:', error)
    else:
        print("Error:", error)

def startGame(request):
    return render(request, "game/intro.html", {})

def pickHybrid(request):
    game = GameProfile()
    game.save()
    request.session['game_id'] = game.id
    context = {}
    hybrid_form = GameProfileForm()
    fert_form = FertilizerInitForm()

    if hybrid_form.is_valid():
        hybrid_form.save()

    context['hybrid_form'] = hybrid_form
    context['fert_form'] = fert_form

    return render(request, "game/hybrid.html", context)

def weeklySelection(request, game_id=None):
    
    context = {}
    matplotlib.pyplot.close()

    if game_id == None:
        game_id = request.session.get('game_id', None) 
    game = GameProfile.objects.get(id=game_id)
    
    global gamePath
    gamePath = f"id-{game_id}"

    gameInputs = {}

    with open("UNLI2309.MZX", 'r') as f:
       gameInputs['MZX_content'] = f.read().split("\n")
            

    start_date = str(int(getDate(gameInputs['MZX_content'])))
    start_day = int(start_date[len(start_date) - 3:])
    date = str(int(start_date) + (((game.week)-1) * 7))

    context = {}
    fert_entry = -1
    if game.hybrid is None and request.POST.get('hybrid') is None:
        return redirect("hybrid")

    if request.method == "POST":

        game.week += 1
        if (game.week == 1):
            request.session['start_date'] = start_date
            game.hybrid = request.POST['hybrid']
            game.seeding_rate = request.POST['seeding_rate']
            gameInputs['MZX_content'] = setSeedingRate(gameInputs['MZX_content'], game.seeding_rate)
            game.weather_type = request.POST['weather_type']

            fertilizer_init = FertilizerInit(week1 = request.POST['week1'], week6 = request.POST['week6'], week9 = request.POST['week9'], week10 = request.POST['week10'], week12 = request.POST['week12'], week14 = request.POST['week14'], week15 = request.POST['week15'])
            fertilizer_init.save()
            game.fert_id = fertilizer_init.id

            gameInputs['WTH_name'] = "NEME0000.WTH"
            gameInputs['WTH_content'] = yearlyRandomizer()

            altForecast = True
            gameInputs['forecast_content'] = altForecastWeather(gameInputs['WTH_content']) if altForecast else forecastWeather(gameInputs['WTH_content'])

            uploadInputs(gameInputs)
            print("WEEK 1 BABY!!!")

        else:
            gameInputs = downloadInputs()
            
            date = str(int(start_date) + (((game.week)-1) * 7))

            fertilizerQuantity = request.POST.get('fertilizer')
            irrigationQuantity = getIrrigation(request)
            
            gameInputs['MZX_content'] = addFertilizer(gameInputs['MZX_content'], fertilizerQuantity, int(date)-7)
            gameInputs['MZX_content'] = addIrrigation(gameInputs['MZX_content'], irrigationQuantity, fertilizerQuantity, int(date)-7)

            computeDSSAT(game.hybrid, gameInputs)

        game.save()
        return redirect("weekly")

    gameInputs = downloadInputs()
    if game.week > 1:
        gameOutputs = downloadOutputs()
        context['aquaspy_graph'] = plotAquaSpy(date, start_day, gameInputs, gameOutputs)
        context['root_depth_graph'] = plotOneAttribute(date, start_day, gameOutputs['OPG_content'], 'RDPD', 'Inches (in)', 'Root Depth')
        context['growth_stage_graph'] = plotOneAttribute(date, start_day, gameOutputs['OPG_content'], 'GSTD', 'Stage', 'Growth Stage')
        context['nitrogen_stress_graph'] = plotOneAttribute(date, start_day, gameOutputs['OPG_content'], 'NSTD', 'N Stress', 'Nitrogen Stress')
        context['water_layer_graph'] = plotWaterLayers(date, start_day, gameOutputs)
        context['weather_history'] = getWeatherHistory(date, start_day, gameInputs)

    gameInputs['MZX_content'] = gameInputs['MZX_content']

    context['week'] = game.week

    iform = IrrigationEntriesForm()
    if iform.is_valid():
        iform.save()
    context['iform'] = iform

    fert_init = FertilizerInit.objects.get(id=game.fert_id)
    fert_entry = fert_init.week1 if game.week == 1 else fert_init.week6 if game.week == 6 else fert_init.week9 if game.week == 9 else fert_init.week10 if game.week == 10 else fert_init.week12 if game.week == 12 else fert_init.week14 if game.week == 14 else fert_init.week15 if game.week == 15 else 0
    context['fert_entry'] = fert_entry
    
    fform = FertilizerEntriesForm1(initial = {'fertilizer': fert_entry}) if game.week <= 6 else FertilizerEntriesForm2(initial = {'fertilizer': fert_entry})
    if fform.is_valid():
        fform.save()

    context['fform'] = fform

    context['weather'] = getWeather(date, gameInputs)

    total_irrigation_cost = getTotalIrrigationCost(gameInputs['MZX_content'], date)
    total_fertilizer_cost = getTotalFertilizerCost(gameInputs['MZX_content'], date)

    context['irr_cost'] = round(total_irrigation_cost, 2)
    context['fert_cost'] = round(total_fertilizer_cost, 2)

    # Insurance + Insecticide + Seeds
    context['other_costs'] = round(142.79, 2)

    context['total_cost'] = round(context['irr_cost'] + context['fert_cost'] + context['other_costs'], 2)
    context['bushel_cost'] = round(context['total_cost']/230, 2)

    matplotlib.pyplot.close()
    
    if (game.week >= 24):
        return redirect("/game/final")
    else:
        return render(request, "game/weekly.html", context)

def finalResults(request):
    
    game_id = request.session.get('game_id', None) 
    game = GameProfile.objects.get(id=game_id)

    context = {}
    
    gameInputs = downloadInputs()
    gameOutputs = downloadOutputs()

    start_date = int(request.session.get('start_date', None))
    start_day = int(str(start_date)[len(str(start_date)) - 3:])
    date = str(start_date + (game.week * 7))

    total_irrigation_cost = round(getTotalIrrigationCost(gameInputs['MZX_content'], date), 2)
    total_fertilizer_cost = round(getTotalFertilizerCost(gameInputs['MZX_content'], date), 2)

    context['irr_cost'] = total_irrigation_cost
    context['fert_cost'] = total_fertilizer_cost
    context['other_costs'] = round(142.79, 2)
    context['total_cost'] = round(total_irrigation_cost + total_fertilizer_cost + context['other_costs'], 2)

    finalYield = getFinalYield(gameOutputs)

    context['bushel_cost'] = round(context['total_cost']/finalYield, 2)
    context['yield'] = finalYield

    
    context['aquaspy_graph'] = plotAquaSpy(date, start_day, gameInputs, gameOutputs)
    context['water_layer_graph'] = plotWaterLayers(date, start_day, gameOutputs)

    # request.session.clear()

    return render(request, "game/final.html", context)
    
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
                newString = " 1 %s IR001%s%s" % (date, beforeSpaces, quantity)
            elif index == 1:
                newString = " 1 %s IR001%s%s" % (date+3, beforeSpaces, quantity)
            irrigationLines.append(newString)

    for i, line in enumerate(text):
        if (line.startswith("@I")):
            onIrrigation = True
        

        if (onIrrigation and line == ""):
            for j, line in enumerate(irrigationLines):
                text.insert(i+j, line)
            return text
    return text

def getTotalIrrigationCost(text, date):
    onIrrigation = False
    totalIrrigationCost = 0

    for line in text:
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
        if (onFertilizer and line == ""):
            newString = " 1 %s FE001 AP001    10%s%s   -99   -99   -99   -99   -99 -99" % (str(date), beforeSpaces, fertilizerQuantity)
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

        
def getWeather(date, gameInputs):
    lowArray = []
    highArray = []
    dateFound = False
    weatherInfo = []

    day = date[len(date) - 3:]

    try:
        for line in gameInputs['forecast_content']:
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

def plotOneAttribute(date, start_day, content, attribute, yaxis, title):

    day = int(date[len(date) - 3:])
    
    readingStress = False

    days = []
    attribute_values = []
    index = -1

    for line in content:
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
    imgdata = io.StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    plt.close()
    
    return data

def getFinalYield(gameOutputs):
    readingVariables = False
    finalYield = -1

    for line in gameOutputs['OOV_content']:
        items = list(filter(None, line.split(" ")))
        if items[0] == '@' and not readingVariables:
            readingVariables = True
        elif readingVariables and items[0].startswith('Yield'):
            finalYield = round(float(items[-2]) / 62.77, 1)
            return finalYield

def plotAquaSpy(date, start_day, gameInputs, gameOutputs):
    
    day = int(date[len(date) - 3:])

    rootArray = getRootDepth(date, gameOutputs)
    if not rootArray:
        return None

    readingSoil = False
    readingFile = False
    index = -1
    soilArray = []

    for line in gameInputs['SOL_content']:
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

    readingWater = False
    index2 = -1
    waterArray = []
    ulimitArray = []
    llimitArray = []
    rootDay = 0

    for line in gameOutputs['OSW_content']:
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
    imgdata = io.StringIO()
    plt.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    plt.close()

    return data

def plotWaterLayers(date, start_day, gameOutputs):
    day = int(date[len(date) - 3:])

    readingWater = False
    layerNum = 12
    waterLayers = [[] for i in range(1,layerNum)]

    for line in gameOutputs['OSW_content']:
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
    imgdata = io.StringIO()
    plt.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()
    plt.close()

    return data

def getRootDepth(date, gameOutputs):
    day = int(date[len(date) - 3:])
    reading = False
    day = 0
    rootArray = []

    for line in gameOutputs['OPG_content']:
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

def getWeatherHistory(date, start_day, gameInputs):
    day = int(date[len(date) - 3:])
    
    history = []

    forecastIndex = -1
    for line in gameInputs['WTH_content']:
        items = line.split(" ")
        items = [x for x in items if x]

        if len(items) == 0 or not items[0].isdigit():
            continue
        else:
            forecastIndex += 1

        forecastItems = gameInputs['forecast_content'][forecastIndex].split(" ")
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

def computeDSSAT(hybrid, gameInputs): 
    
    # try:  
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(gameInputs['MZX_name'], "\n".join(gameInputs['MZX_content']))
        zip_file.writestr(gameInputs['SOL_name'], "\n".join(gameInputs['SOL_content']))
        zip_file.writestr(gameInputs['WTH_name'], "\n".join(gameInputs['WTH_content']))
        zip_file.writestr('command.ps1', "../../DSCSM048 %s A %s" % (hybrid, gameInputs['MZX_name']))

    zip_buffer.seek(0)     

    # Upload to S3
    s3.delete_object(Bucket='outputvtapsbucket', Key=f"{gamePath}/{gamePath}.zip")  
    s3.upload_fileobj(zip_buffer, 'vtapsbucket', f"{gamePath}.zip")


    file_present = False

    bucket = None
    timeout = time.time() + 60*5

    while not file_present:
        try:
            bucket = s3.list_objects_v2(
                Bucket='outputvtapsbucket',
                Prefix =gamePath,
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

    gameOutputs = downloadOutputs()

    return gameOutputs

def uploadInputs(gameInputs):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        if 'MZX_name' not in gameInputs:
            with open("UNLI2309.MZX", 'r') as f:
                contents = f.read()
                zip_file.writestr("UNLI2309.MZX", contents)
        else:
            zip_file.writestr(gameInputs['MZX_name'], "\n".join(gameInputs['MZX_content']))
        
        if 'SOL_name' not in gameInputs:
            with open("NE.SOL", 'r') as f:
                contents = f.read()
                zip_file.writestr("NE.SOL", contents)
        else:
            zip_file.writestr(gameInputs['SOL_name'], "\n".join(gameInputs['SOL_content']))


        zip_file.writestr(gameInputs["WTH_name"], "\n".join(gameInputs["WTH_content"]))
        zip_file.writestr("forecast.txt", "\n".join(gameInputs["forecast_content"]))

    zip_buffer.seek(0)

    # Upload to S3
    s3.upload_fileobj(zip_buffer, 'vtapsgamedata', f"{gamePath}.zip")


def downloadInputs():
    zip_buffer = io.BytesIO()
    s3.download_fileobj('vtapsgamedata', f"{gamePath}.zip", zip_buffer)
    zip_buffer.seek(0)
    data = {}
    with zipfile.ZipFile(zip_buffer) as zipFile:
        for name in zipFile.namelist():
            if name[-4:] == '.MZX':
                data['MZX_name'] = name
                data['MZX_content'] = zipFile.read(name).decode('utf-8').split("\n")
            elif name[-4:] == '.SOL':
                data['SOL_name'] = name
                data['SOL_content'] = zipFile.read(name).decode('utf-8').split("\n")
            elif name[-4:] == '.WTH':
                data['WTH_name'] = name
                data['WTH_content'] = zipFile.read(name).decode('utf-8').split("\n")
            elif name == 'forecast.txt':
                data['forecast_content'] = zipFile.read(name).decode('utf-8').split("\n")

    return data

def downloadOutputs():
    zip_buffer = io.BytesIO()
    print("DOWNLOAD GAME PATH:", gamePath)
    s3.download_fileobj('outputvtapsbucket', f"{gamePath}/{gamePath}.zip", zip_buffer)
    data = {}
    with zipfile.ZipFile(zip_buffer) as zipFile:
        for name in zipFile.namelist():
            if name[-4:] == '.OPG':
                data['OPG_name'] = name
                data['OPG_content'] = zipFile.read(name).decode('utf-8').split("\n")
            elif name[-4:] == '.OOV':
                data['OOV_name'] = name
                data['OOV_content'] = zipFile.read(name).decode('utf-8').split("\n")
            elif name[-4:] == '.OSW':
                data['OSW_name'] = name
                data['OSW_content'] = zipFile.read(name).decode('utf-8').split("\n")
            # elif name == f"{gamePath}\\WARNING.OUT":
            #     print("\n".join(zipFile.read(name).decode('utf-8').split("\n")))

    return data