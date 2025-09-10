#!/usr/local/bin/python3

from django.shortcuts import render, redirect
import os
import time
from game.forms import IrrigationEntriesForm, FertilizerEntriesForm1, FertilizerEntriesForm2, GameProfileForm, FertilizerInitForm
from .models import GameProfile, FertilizerInit
from teacher.models import Game
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')
import io
import zipfile
import boto3
import environ
import watchtower, logging
from .functions.functions import *
from .functions.fileSearch import *
import pandas as pd
import csv
from django.http import HttpResponseRedirect

environment = os.environ['ENV']

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
        print('Error:', error)

def runGame(request, game_id=None):
    game_url = f'/game/{game_id}' if game_id is not None else '/game'
    context = {'game_url': game_url}
    
    try:
        if game_id is None:   
            game_id = request.session.get('game_id', None) 
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        if game_id is None:
            game = Game()
            game.save()
        else:
            return redirect("/")

    if request.user.is_authenticated:
        user = request.user
    else:
        user = None

    try:
        gameProfile = GameProfile.objects.get(game=game, user=user)

        if gameProfile.hybrid is None and request.POST.get('hybrid') is None:
            hybrid_form = GameProfileForm()
            fert_form = FertilizerInitForm()

            if hybrid_form.is_valid():
                hybrid_form.save()

            if fert_form.is_valid():
                fert_form.save()

            context['hybrid_form'] = hybrid_form
            context['fert_form'] = fert_form
            return render(request, "game/init.html", context)
        else:
            if gameProfile.week < 22 and not gameProfile.finished:
            # if gameProfile.week <= 12 and not gameProfile.finished:
                context = weeklySelection(request, gameProfile)
                if context is None:
                    return redirect(game_url)
                # elif "computing" in context or "computing" not in context:
                # elif "computing" in context:
                #     return render(request, "game/standby.html", context)
                else:
                    return render(request, "game/weekly.html", context)
            else:
                context = finalResults(request, gameProfile)
                return render(request, "game/final.html", context)
    except GameProfile.DoesNotExist:
        gameProfile = GameProfile(game=game, user=user)
        gameProfile.save()
        if game_id is None:
            request.session['game_id'] = game.id
        # return render(request, "game/intro.html", context)
        return redirect(game_url)

def weeklySelection(request, game):
    context = {}
    
    gamePath = f"id-{game.id}"
            
    gameInputs = {}

    with open("UNLI2309.MZX", 'r') as f:
        gameInputs['MZX_content'] = f.read().split("\n")
        gameInputs['MZX_name'] = 'UNLI2309.MZX'

    start_date = str(int(getDate(gameInputs['MZX_content'])))
    start_day = int(start_date[len(start_date) - 3:])
    date = str(int(start_date) + (((game.week)) * 7))

    context = {}
    fert_entry = -1

    if request.method == "POST":
        if game.computing:
            time.sleep(3)
            return None
        if (game.week == 11) or not game.initialized or 'hybrid' in request.POST:

            request.session['start_date'] = start_date
            game.hybrid = request.POST['hybrid']
            game.seeding_rate = request.POST['seeding_rate']
            gameInputs['MZX_content'] = setSeedingRate(gameInputs['MZX_content'], game.seeding_rate)
            game.team_id = request.POST['team_id']

            fertilizer_init = FertilizerInit(week1 = request.POST['week1'], week6 = request.POST['week6'], week9 = request.POST['week9'], week10 = request.POST['week10'], week12 = request.POST['week12'], week14 = request.POST['week14'], week15 = request.POST['week15'])
            gameInputs['MZX_content'] = addFertilizer(gameInputs['MZX_content'], request.POST['week1'], int(start_date) + (0 * 7))
            gameInputs['MZX_content'] = addFertilizer(gameInputs['MZX_content'], request.POST['week6'], int(start_date) + (5 * 7))
            gameInputs['MZX_content'] = addFertilizer(gameInputs['MZX_content'], request.POST['week9'], int(start_date) + (8 * 7))
            gameInputs['MZX_content'] = addFertilizer(gameInputs['MZX_content'], request.POST['week10'], int(start_date) + (9 * 7))
            gameInputs['MZX_content'] = addIrrigation(gameInputs['MZX_content'], [0.75], 0, int(start_date) + (6 * 7), 7)
            gameInputs['MZX_content'] = addIrrigation(gameInputs['MZX_content'], [0.75], 0, int(start_date) + (7 * 7), 8)
            gameInputs['MZX_content'] = addIrrigation(gameInputs['MZX_content'], [0.75], 0, int(start_date) + (8 * 7), 9)
            gameInputs['MZX_content'] = addIrrigation(gameInputs['MZX_content'], [0.75], 0, int(start_date) + (9 * 7), 10)
            gameInputs['MZX_content'] = addIrrigation(gameInputs['MZX_content'], [0.75], 0, int(start_date) + (10 * 7), 11)
            fertilizer_init.save()
            game.fert_id = fertilizer_init.id

            gameInputs['WTH_name'] = "NEME0000.WTH"
            # gameInputs['WTH_content'] = yearlyRandomizer()
            file = open("weather_files/NEME1901.WTH")
            gameInputs['WTH_content'] = forecastWeather(file.read().split("\n"))
            file.close()

            altForecast = True
            # gameInputs['forecast_content'] = altForecastWeather(gameInputs['WTH_content']) if altForecast else forecastWeather(gameInputs['WTH_content'])
            gameInputs['forecast_content'] = gameInputs['WTH_content']
            uploadInputs(gameInputs, gamePath)
            game.initialized = True
            game.week = 11
            gameInputs = downloadInputs(gamePath)

        else:
            game.computing = True
            game.save()
            gameInputs = downloadInputs(gamePath)

            fertilizerQuantity = request.POST.get('fertilizer')
            irrigationQuantity = getIrrigation(request)
            
            gameInputs['MZX_content'] = addFertilizer(gameInputs['MZX_content'], fertilizerQuantity, int(date)-7)
            gameInputs['MZX_content'] = addIrrigation(gameInputs['MZX_content'], irrigationQuantity, fertilizerQuantity, int(date)-7, game.week)
        computeDSSAT(game.hybrid, gameInputs, gamePath)

        game.week += 1
        game.save()
        return None
    
    gameInputs = downloadInputs(gamePath)
    
    if game.week > 11:
        gameOutputs = downloadOutputs(gamePath)
        if gameOutputs is False:
            time.sleep(3)
            return None
        game.computing = False
        game.save()
        context['aquaspy_graph'] = plotAquaSpy(date, start_day, gameInputs, gameOutputs)[0]
        context['root_depth_graph'] = plotOneAttribute(date, start_day, gameOutputs['OPG_content'], 'RDPD', 'Inches (in)', 'Root Depth')
        context['growth_stage_graph'] = plotOneAttribute(date, start_day, gameOutputs['OPG_content'], 'GSTD', 'Stage', 'Growth Stage')
        context['nitrogen_stress_graph'] = plotOneAttribute(date, start_day, gameOutputs['OPG_content'], 'NSTD', 'N Stress', 'Nitrogen Stress')
        context['water_layer_graph'] = plotWaterLayers(date, start_day, gameOutputs)
        
        historyDict = getHistory(date, start_day, gameInputs, gameOutputs)
        history = historyDict['history']
        recentHistory = historyDict['recentHistory']
        context['weekly_rain'] = round(sum(recentHistory['rain']), 2)
        context['total_rain'] = round(sum(history['rain']), 2)
        context['weekly_et'] = round(sum(recentHistory['et']), 2)
        context['total_et'] = round(sum(history['et']), 2)
        context['weekly_irr'] = round(sum(recentHistory['irr']), 2)
        context['total_irr'] = round(sum(history['irr']), 2)
        context['weekly_fert'] = round(sum(recentHistory['fert']), 2)
        context['total_fert'] = round(sum(history['fert']), 2)
        

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
    context['other_costs'] = round(742.79, 2)

    context['total_cost'] = round(context['irr_cost'] + context['fert_cost'] + context['other_costs'], 2)
    context['bushel_cost'] = round(context['total_cost']/230, 2)
    
    return context

def finalResults(request, game):

    context = {}
    gamePath = f"id-{game.id}"
    
    gameInputs = downloadInputs(gamePath)
    gameOutputs = downloadOutputs(gamePath)

    start_date = int(request.session.get('start_date', None))
    start_day = int(str(start_date)[len(str(start_date)) - 3:])
    date = str(start_date + (game.week * 7))

    total_irrigation_cost = round(getTotalIrrigationCost(gameInputs['MZX_content'], date), 2)
    total_fertilizer_cost = round(getTotalFertilizerCost(gameInputs['MZX_content'], date), 2)

    context['irr_cost'] = total_irrigation_cost
    context['fert_cost'] = total_fertilizer_cost
    context['other_costs'] = round(742, 2)
    context['total_cost'] = round(total_irrigation_cost + total_fertilizer_cost + context['other_costs'], 2)

    finalYield = getFinalYield(gameOutputs)
    history = getHistory(date, start_day, gameInputs, gameOutputs)['history']

    context['bushel_cost'] = round(context['total_cost']/finalYield, 2)
    context['yield'] = finalYield

    
    context['aquaspy_graph'], yAxis = plotAquaSpy(date, start_day, gameInputs, gameOutputs)
    context['nitrogen_stress_graph'] = plotOneAttribute(date, start_day, gameOutputs['OPG_content'], 'NSTD', 'N Stress', 'Nitrogen Stress')



    controlGameInputs = gameInputs.copy()
    with open(controlGameInputs['MZX_name'], 'r') as f:
        controlGameInputs['MZX_content'] = f.read().split("\n")

    controlGamePath = gamePath + 'control'
     
    if checkBucket(controlGamePath) == False:
        computeDSSAT(game.hybrid, controlGameInputs, controlGamePath)
    controlGameOutputs = downloadOutputs(controlGamePath)

    controlFinalYield = getFinalYield(controlGameOutputs)
    controlHistory = getHistory(date, start_day, controlGameInputs, controlGameOutputs)['history']

    WNIPI_yield = ((finalYield / controlFinalYield) - 1)
    WNIPI_irr = (1 + (sum(history['irr']) / sum(controlHistory['et'])))
    WNIPI_N = getNitrogenUptake(date, controlGameOutputs)
    WNIPI_total = (WNIPI_yield / (WNIPI_irr * WNIPI_N))
    context['WNIPI'] = round(WNIPI_total, 4)

    context['irr_amount'] = sum(history['irr'])
    context['fert_amount'] = sum(history['fert'])
    context['et_amount'] = sum(history['et'])
    context['rain_amount'] = sum(history['rain'])

    context['control_aquaspy_graph'] = plotAquaSpy(date, start_day, controlGameInputs, controlGameOutputs, yAxis)[0]
    context['control_nitrogen_stress_graph'] = plotOneAttribute(date, start_day, controlGameOutputs['OPG_content'], 'NSTD', 'N Stress', 'Nitrogen Stress')

    game.finished = True
    game.save()

    csv = createCSV(game.team_id, context['irr_amount'], context['fert_amount'], context['yield'], context['bushel_cost'], context['WNIPI'])
    s3.put_object(
        Bucket="finalresultsbucket",
        Key=f"{gamePath}/final_summary-{game.team_id}.csv",
        Body=csv,
        ContentType="text/csv",
        ContentDisposition=f'attachment; filename="vtaps_game_{game.id}_summary.csv"',
    )

    return context

def downloadResults(request, game_id=None):
    try:
        if game_id is None:   
            game_id = request.session.get('game_id', None) 
        game = Game.objects.get(id=game_id)      
    except Game.DoesNotExist:
        return redirect("/")
    
    if request.user.is_authenticated:
        user = request.user
    else:
        user = None

    try:
        gameProfile = GameProfile.objects.get(game=game, user=user)
        if not gameProfile.finished:
            return redirect("/")  
    except GameProfile.DoesNotExist:
        return redirect("/")
      
    gamePath = f"id-{gameProfile.id}"
    key = f"{gamePath}/final_summary-{gameProfile.team_id}.csv"


    presigned = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": "finalresultsbucket", "Key": key},
        ExpiresIn=60
    )
    return HttpResponseRedirect(presigned)

    
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
        
def addIrrigation(text, irrigationQuantity, fertilizerQuantity, date, week):
    onIrrigation = False

    irrigationLines = []

    for index, quantity in enumerate(irrigationQuantity):
        quantity = float(quantity)
        if index == 0 and week > 6:
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
    dateFound = False
    weatherInfo = []

    day = date[len(date) - 3:]

    try:
        for line in gameInputs['forecast_content']:
            items = list(filter(None, line.split(" ")))
            items = [x for x in items if x]
            
            weatherDay = items[0][len(items[0]) - 3:]

            if weatherDay == day:
                dateFound = True

            if dateFound:
                weatherDateConversion = "\n" + datetime.strptime("2025-" + weatherDay, "%Y-%j").strftime("%m-%d-%Y")
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

                rainQuant = mmToInches(float(items[3]))
                if rainQuant < 0:
                    rainQuant = 0
                
                weatherData = {"day": weatherDateConversion, "tHigh": round((float(items[1]) * (9/5)) + 32, 1), "tLow": round((float(items[2]) * (9/5)) + 32, 1), "pRain": rainQuant}

                weatherInfo.append(weatherData)

                if int(weatherDay) - int(day) >= 6:
                    dateFound = False
                    return weatherInfo
    
    except Exception as error:
        if environment == 'prod':
            logger.info(error)
        else:
            print('getWeather error:', error)

# def getRecap(date, gameInputs):
#     dateFound = False
#     weatherInfo = []

#     day = date[len(date) - 3:]

#     try:
#         for index, line in enumerate(gameInputs['forecast_content']):
#             items = list(filter(None, line.split(" ")))
#             items = [x for x in items if x]
            
#             weatherDay = items[0][len(items[0]) - 3:]

#             if weatherDay == day:
#                 dateFound = True

#             if dateFound:
#                 wth_row = list(filter(None, gameInputs['WTH_content'][index].split(" ")))
#                 weatherData = {"fHigh": round(float(items[2]) * (9/5) + 32, 1), "fLow": round(float(items[3]) * (9/5) + 32, 1), "fRain": mmToInches(float(items[4])), "aHigh": round(float(wth_row[2]) * (9/5) + 32, 1), "aLow": round(float(wth_row[3]) * (9/5) + 32, 1), "aRain": mmToInches(float(wth_row[4]))}

#                 weatherInfo.append(weatherData)

#                 if int(weatherDay) - int(day) >= 6:
#                     dateFound = False
#                     return weatherInfo
    
#     except Exception as error:
#         if environment == 'prod':
#             logger.info(error)
#         else:
#             print('getWeather error:', error)

def mmToInches(mm):
    inches = round(float(0.0393701 * mm), 2)
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
                attribute_values.append(mmToInches(float(items[index]) * 1000))
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
    if attribute == 'GSTD':
        ax.set_yticks([0, 1, 2, 3, 4, 5])
        ax.set_yticklabels(['VE', 'V3-V8', 'VT-R1', 'R2-R3', 'R4-R5', 'R6'])
    fig.suptitle(title, fontsize=16)
    imgdata = io.StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    plt.close(fig)
    
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
            finalYield = finalYield / 0.845                     #Based on Rintu's Calibration (9/8/2025)
            return finalYield

def plotAquaSpy(date, start_day, gameInputs, gameOutputs, yAxis=-1):
    
    day = int(date[len(date) - 3:])

    start_day = int(start_day)

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

    fig, ax = plt.subplots()

    # ax.plot(limitRange, ulimitArray, color="indigo")
    # ax.plot(limitRange, llimitArray, color="goldenrod")
    ax.plot(waterRange, waterArray, color="black")
    ax.legend(["Soil Water"])
    ax.fill_between(limitRange, ulimitArray, llimitArray, alpha=alpha)
    ax.set_xlabel('Days since planting')
    ax.set_ylabel("Soil Water (in)")
    ax.set_title("Cumulative Soil Water", fontsize=16)
    if yAxis != -1:
        ax.set_ylim([0, yAxis])
    else:
        ax.set_ylim(bottom=0)
    imgdata = io.StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    yAxis = plt.ylim()[1]

    plt.close(fig)

    return data, yAxis

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
        ax.plot(layer)
    ax.set_xlabel('Days since planting')
    ax.set_ylabel("Soil Water Layer")
    ax.set_yticks([])
    ax.legend(legendLayers, loc="upper right", bbox_to_anchor = (1.25, 1))
    # plt.yticks(range(1, layerNum+1), soilVolumes)
    ax.set_title("Soil Water By Depth", fontsize=16)
    imgdata = io.StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()
    plt.close(fig)

    return data

def getRootDepth(date, gameOutputs):
    day = int(date[len(date) - 3:])
    reading = False
    rootArray = []

    for line in gameOutputs['OPG_content']:
        items = list(filter(None, line.split(" ")))
        if len(items) <= 33:
            continue 
        elif not reading and items[0] == "@YEAR":
            reading = True
        elif reading:
            rootArray.append(mmToInches(float(items[33]) * 1000))
            if int(items[1]) == day:
                return rootArray
        
    return rootArray

def getHistory(date, start_day, gameInputs, gameOutputs):
    
    day = int(date[len(date) - 3:])
    date = int(date) - 7
    history = {"rain": [0.0], "et": [0.0], "irr": [0.0], "fert": [0.0]}
    recentHistory = {"rain": [0.0], "et": [0.0], "irr": [0.0], "fert": [0.0]}

    for line in gameInputs['WTH_content']:
        items = line.split(" ")
        items = [x for x in items if x]

        if len(items) == 0 or not items[0].isdigit():
            continue

        currDay = int(items[0][len(items[0]) - 3:])
        if currDay < start_day:
            continue
        elif currDay >= day:
            break
        else:
            rain = mmToInches(float(items[3]))
            history['rain'].append(rain)
            if currDay >= day - 7:
                recentHistory['rain'].append(rain)
    
    onIrrigation = False
    onFertilizer = False

    for line in gameInputs['MZX_content']:
        items = line.split(" ")
        items = [x for x in items if x]
        if (len(items) < 1):
            if (onFertilizer):
                break
            else:
                onFertilizer = False
                onIrrigation = False
                continue

        elif (len(items) >= 4 and items[3] == "IRVAL"):
            onIrrigation = True
            onFertilizer = False

        elif (onIrrigation):
            if (int(items[1]) < int(date)):
                irrigation = mmToInches(float(items[3]))
                history['irr'].append(irrigation)
                if (int(items[1]) >= int(date) - 7):
                    recentHistory['irr'].append(irrigation)
            
        elif (len(items) >= 6 and items[5] == "FAMN"):
            onIrrigation = False
            onFertilizer = True

        elif (onFertilizer):
            if (int(items[1]) < int(date)):
                fertilizer = float(items[5])
                history['fert'].append(fertilizer)
                if (int(items[1]) >= int(date) - 7):
                    recentHistory['fert'].append(fertilizer)

    for line in gameOutputs['OEB_content']:
        items = line.split(" ")
        items = [x for x in items if x]

        if len(items) == 0 or not items[0].isdigit():
            continue
        
        currDay = int(items[1][len(items[1]) - 3:])
        if currDay < start_day:
            continue
        elif currDay >= day:
            break
        else:
            history['et'].append(mmToInches(float(items[10])))
            if currDay >= day - 7:
                recentHistory['et'].append(mmToInches(float(items[10])))
    
    return {"history": history, "recentHistory": recentHistory}


def getNitrogenUptake(date, gameOutputs):
    day = int(date[len(date) - 3:])
    reading = False
    day = 0
    nitrogenUptake = 0

    for line in gameOutputs['OPN_content']:
        items = list(filter(None, line.split(" ")))
        if len(items) <= 5:
            continue 
        elif not reading and items[0] == "@YEAR":
            reading = True
        elif reading:
            nitrogenUptake = float(items[5])
            if int(items[1]) == day:
                return nitrogenUptake
        
    return nitrogenUptake

# def getWeatherHistory(date, start_day, gameInputs, gameOutputs):
#     day = int(date[len(date) - 3:])
    
#     history = []

#     forecastIndex = -1
#     for line in gameInputs['WTH_content']:
#         items = line.split(" ")
#         items = [x for x in items if x]

#         if len(items) == 0 or not items[0].isdigit():
#             continue
#         else:
#             forecastIndex += 1

#         forecastItems = gameInputs['forecast_content'][forecastIndex].split(" ")
#         forecastItems = [x for x in forecastItems if x]
#         tempDay = int(items[0][len(items[0]) - 3:])
#         if tempDay < start_day:
#             continue
#         elif tempDay >= day:
#             break
#         else:
#             weatherDict = {"day": tempDay, "high": round(float(items[2]) * (9/5) + 32, 1), "low": round(float(items[3]) * (9/5) + 32, 1), "rain": mmToInches(float(items[4])), "forecast_high": round(float(forecastItems[2]) * (9/5) + 32, 1), "forecast_low": round(float(forecastItems[3]) * (9/5) + 32, 1), "forecast_rain": mmToInches(float(forecastItems[4]))}
#             history.append(weatherDict)
#     return history

def computeDSSAT(hybrid, gameInputs, gamePath): 
    
    uploadInputs(gameInputs, gamePath) 
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

def checkOutputs(gamePath):

    timeout = time.time() + (60*10)

    while time.time() < timeout:
        if checkBucket(gamePath):
            return True
        time.sleep(0.1)
    
    return False

def checkBucket(gamePath):

    key = f'{gamePath}/{gamePath}.zip'

    try:
        s3.head_object(Bucket='outputvtapsbucket', Key=key)
        return True
    except:
        return False

def uploadInputs(gameInputs, gamePath):

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


def downloadInputs(gamePath):
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

def downloadOutputs(gamePath):

    outputStatus = checkOutputs(gamePath)
    if outputStatus is False:
        return False
    
    try:
        zip_buffer = io.BytesIO()
        s3.download_fileobj('outputvtapsbucket', f"{gamePath}/{gamePath}.zip", zip_buffer)
        zip_buffer.seek(0) 
        data = {}
        with zipfile.ZipFile(zip_buffer) as zipFile:
            for name in zipFile.namelist():
                content = zipFile.read(name).decode('utf-8').split("\n")
                name = name.split("\\")[1]
                # with open(f'exampleOutput/{name}', 'w') as f:
                #     f.write("\n".join(content))

                if name[-4:] == '.OPG':
                    data['OPG_name'] = name
                    data['OPG_content'] = content
                elif name[-4:] == '.OOV':
                    data['OOV_name'] = name
                    data['OOV_content'] = content
                elif name[-4:] == '.OSW':
                    data['OSW_name'] = name
                    data['OSW_content'] = content
                elif name[-4:] == '.OEB':
                    data['OEB_name'] = name
                    data['OEB_content'] = content
                elif name[-4:] == '.OPN':
                    data['OPN_name'] = name
                    data['OPN_content'] = content

        return data
    except:
        return False
    
def createCSV(team_id, irr_total, fert_total, final_yield, final_bushel_cost, final_wnipi):
    buf = io.StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(["Team ID", "Irrigation Total", "Fertilizer Total", "Final Yield", "Cost Per Bushel", "WNIPI Score"])
    writer.writerow([team_id, irr_total, fert_total, final_yield, final_bushel_cost, final_wnipi])
    return buf.getvalue().encode("utf-8-sig")

def getRainiest():
    weatherFiles = os.listdir("weather_files")
    finalName = ""
    finalSum = 0
    for file in weatherFiles:
        fullPath = os.path.join("weather_files", file)
        with open(fullPath, 'r') as file:
            content = file.read().split("\n")
            tempSum = 0

            for line in content:
                items = list(filter(None, line.split(" ")))
                if len(items) > 5 and items[0].isnumeric():
                    tempSum += float(items[4])

            if tempSum > finalSum:
                finalSum = tempSum
                finalName = fullPath
    print("RAINIEST NAME:", finalName)