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

env = environ.Env()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

def startGame(request):
    user = SingleplayerProfile()
    user.save()
    request.session['user_id'] = user.id
    return render(request, "singleplayer/home.html", {})

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
    # Session.objects.all().delete()

    matplotlib.pyplot.close()
    user_id = request.session.get('user_id', None) 
    user = SingleplayerProfile.objects.get(id=user_id)
    if (user.week >= 24):
        return redirect("/singleplayer/final")
    
    controlFile = 'UNLI2201.MZX'
    file = open(controlFile, 'r')
    text = file.readlines()
    file.close()
    
    start_date = str(int(getDate(text)))
    date = str(int(start_date) + (((user.week)-1) * 7))

    context = {}
    fert_entry = -1

    if not os.path.exists("id-%s" % user_id):
        createDirectory(user_id)
    
    if not os.getcwd().split("/")[-1] == "id-%s" % user_id:
        os.chdir("id-%s" % user_id)

    if (request.POST.get('hybrid') != None):
        user.hybrid = request.POST['hybrid']
        user.seeding_rate = request.POST['seeding_rate']
        user.week = 1
        user.weather_type = request.POST['weather_type']

        fertilizer_init = FertilizerInit(week1 = request.POST['week1'], week6 = request.POST['week6'], week9 = request.POST['week9'], week10 = request.POST['week10'], week12 = request.POST['week12'], week14 = request.POST['week14'], week15 = request.POST['week15'])
        fertilizer_init.save()
        user.fert_id = fertilizer_init.id

        user.save()

        compileWeather()

        fert_entry = request.POST['week1']

    elif len(request.POST.keys()) > 0:

        user.week += 1
        user.save()

        file = open(controlFile, 'r')
        text = file.readlines()
        file.close()

        fertilizerQuantity = request.POST.get('fertilizer')
        irrigationQuantity = getIrrigation(request)
        
        text = addFertilizer(text, fertilizerQuantity, int(date)-7)
        text = addIrrigation(text, irrigationQuantity, int(date)-7)

        newText = "".join(text)

        file2 = open(controlFile, 'w')
        file2.write(newText)
        file2.close()

        computeDSSAT(user_id, user.hybrid, controlFile)

    context['week'] = user.week
    
    fert_init = FertilizerInit.objects.get(id=user.fert_id)
    fert_entry = fert_init.week6 if user.week == 6 else fert_init.week9 if user.week == 9 else fert_init.week10
    context['fert_entry'] = fert_entry

    iform = IrrigationEntriesForm()
    if iform.is_valid():
        iform.save()

    context['iform'] = iform

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
        context['aquaspy'] = plotAquaSpy(date, start_day)


    # totals = getEconomics(date)
    # context['waterTotal'] = totals[0]
    # context['fertTotal'] = totals[1]

    # context['graph'] = plotRoots(date, start_day, user_id)
    # context['SWgraph'] = plotSoilWater(date, start_day)

    # context['water_stress_graph1'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'WSPD', 'Percent stress', 'Water Stress Photosynthesis')
    # context['water_stress_graph2'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'WSGD', 'Percent stress', 'Water Stress Expansion')
    # context['nitrogen_stress_graph'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'NSTD', 'Percent stress', 'Nitrogen Stress')

    
    # context['cum_precip_graph'] = plotOneAttribute(date, start_day, 'SoilWat.OUT', 'PREC', 'mm', 'Cumulative Precipitation')
    # context['cum_irrigation_graph'] = plotOneAttribute(date, start_day, 'SoilWat.OUT', 'IRRC', 'mm', 'Cumulative Irrigation')
    # context['total_soil_water_graph'] = plotOneAttribute(date, start_day, 'SoilWat.OUT', 'SWTD', 'mm', 'Total Soil Water')

    # context['leached_nitrogen_graph'] = plotOneAttribute(date, start_day, 'SoilNi.OUT', 'NLCC', 'kg [N] / ha', 'Cumulative Nitrogen Leached')

    matplotlib.pyplot.close()
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
    
    # context['leaf_weight_graph'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'LWAD', 'kg [dm] / ha', 'Leaf Weight')
    # context['stem_weight_graph'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'SWAD', 'kg [dm] / ha', 'Stem Weight')
    # context['grain_weight_graph'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'GWAD', 'kg [dm] / ha', 'Grain Weight')
    # context['root_weight_graph'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'RWAD', 'kg [dm] / ha', 'Root Weight')
    # context['tops_weight_graph'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'CWAD', 'kg [dm] / ha', 'Tops Weight')
    # context['pod_weight_graph'] = plotOneAttribute(date, start_day, 'PlantGro.OUT', 'PWAD', 'kg [dm] / ha', 'Pod Weight')

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

        if (onFertilizer):
            if (lines[0].startswith("*") or lines[0].startswith("@")):
                break
            elif (int(lines[1]) < int(date)):
                if (i - startIndex < 3):
                    totalFertilizerCost += (float(lines[5]) * 0.6) + 8.50
                else:
                    totalFertilizerCost += (float(lines[5]) * 0.6) + 1.25
            else:
                break

        if (lines[5] == "FAMN"):
            onFertilizer = True
            startIndex = i

    return totalFertilizerCost
        
def compileWeather():

    lowArray = []
    highArray = []
    rainArray = []

    weather_file = open("NENP2201.WTH", 'r')
    weather_text = weather_file.readlines()
    weather_file.close()

    forecast_file = open("forecast.txt", 'w')

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

        high_forecast = str(forecastData(highArray))
        low_forecast = str(forecastData(lowArray))
        rain_forecast = str(forecastData(rainArray))


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

def forecastData(previousArray):
    mean = np.mean(previousArray)
    std = np.std(previousArray)
    value = np.random.normal(mean, std/2, 1)
    return(value[0])

# def forecastRain(day):
#     total = 0
#     zeroes = 0


#     forecastArray = []
#     directory = os.fsencode("weather_files")

#     for file in os.listdir(directory):
#         filename = "weather_files/" + os.fsdecode(file)
#         file = open(filename, 'r')
#         text = file.readlines()
#         file.close()

#         for line in text:
#             items = list(filter(None, line.split(" ")))

#             if len(items) > 0:
#                 weatherDate = items[0]

#                 if not weatherDate.isnumeric():
#                     continue

#                 weatherDay = weatherDate[len(weatherDate) - 3:]
#                 if weatherDay == day and len(items) > 4:
#                     rainValue = float(items[4].strip())
#                     forecastArray.append(rainValue)
#                     total += 1
#                     if rainValue == 0.0:
#                         zeroes += 1
#                     else:
#                         forecastArray.append(rainValue)
#                     break
    

#     prediction = -1
#     if zeroes / total >= 0.75:
#         prediction = 0.0
#     else:
#         while np.sign(prediction) == -1:
#             mean = np.mean(forecastArray)
#             std = np.std(forecastArray)
#             prediction = mmToInches(np.random.normal(mean, std/2, 1))
#     return prediction + 0.0

def mmToInches(mm):
    inches = round(float(0.0393701 * mm), 1)
    return inches

def inchesToMM(inches):
    mm = round(float(25.4 * inches), 1)
    return str(mm)

def plotRoots(date, start_day):
    file = open('PlantGro.OUT', 'r')
    text = file.readlines()
    file.close()

    day = int(date[len(date) - 3:])
    
    readingRoots = False

    rootData_Days = []
    rootData_RL1D = []
    rootData_RL2D = []
    rootData_RL3D = []
    rootData_RL4D = []
    rootData_RL5D = []
    rootData_RL6D = []
    rootData_RL7D = []
    rootData_RL8D = []
    rootData_RL9D = []
    rootData_RL10D = []

    for line in text:
        items = list(filter(None, line.split(" ")))
        if len(items) == 0 and not readingRoots:
            continue
        elif readingRoots and len(items) == 0 or readingRoots and int(items[1]) > day:
            break
        elif len(items) > 0 and not readingRoots:
            if (items[0] == "@YEAR"):
                readingRoots = True
        elif len(items) > 1 and readingRoots:
            adjusted_day = int(items[1]) - start_day
            rootData_Days.append(adjusted_day)
            rootData_RL1D.append(float(items[34]))
            rootData_RL2D.append(float(items[35]))
            rootData_RL3D.append(float(items[36]))
            rootData_RL4D.append(float(items[37]))
            rootData_RL5D.append(float(items[38]))
            rootData_RL6D.append(float(items[39]))
            rootData_RL7D.append(float(items[40]))
            rootData_RL8D.append(float(items[41]))
            rootData_RL9D.append(float(items[42]))
            rootData_RL10D.append(float(items[43]))
    
    stackRange = range(int(rootData_Days[0]), int(rootData_Days[-1])+1)

    #REFERENCE FOR CODE TO DISPLAY GRAPH IN TEMPLATE: https://stackoverflow.com/questions/40534715/how-to-embed-matplotlib-graph-in-django-webpage
    fig, ax = plt.subplots()
    ax.stackplot(stackRange, rootData_RL1D, rootData_RL2D, rootData_RL3D, rootData_RL4D, rootData_RL5D, rootData_RL6D, rootData_RL7D, rootData_RL8D, rootData_RL9D, rootData_RL10D, labels=['0-5cm', '5-15cm', '15-23cm', '23-38cm', '38-53cm', '53-61cm', '61-69cm', '69-84cm', '84-99cm', '99-160cm'])
    ax.legend(loc='upper left')
    ax.set_xlabel('Days since planting')
    ax.set_ylabel('Root density cm^3')
    fig.suptitle('Root Density by Depth', fontsize=16)
    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()
    return data

def plotSoilWater(date, start_day):
    file = open('SoilWat.OUT', 'r')
    text = file.readlines()
    file.close()

    day = int(date[len(date) - 3:])
    
    readingRoots = False

    rootData_Days = []
    rootData_RL1D = []
    rootData_RL2D = []
    rootData_RL3D = []
    rootData_RL4D = []
    rootData_RL5D = []
    rootData_RL6D = []
    rootData_RL7D = []
    rootData_RL8D = []
    rootData_RL9D = []
    rootData_RL10D = []

    for line in text:
        items = list(filter(None, line.split(" ")))
        if len(items) == 0 and not readingRoots:
            continue
        elif readingRoots and len(items) == 0 or readingRoots and int(items[1]) > day:
            break
        elif len(items) > 0 and not readingRoots:
            if (items[0] == "@YEAR"):
                readingRoots = True
        elif len(items) > 1 and readingRoots and start_day <= int(items[1]):
            adjusted_day = int(items[1]) - start_day
            rootData_Days.append(adjusted_day)
            rootData_RL1D.append(float(items[17]))
            rootData_RL2D.append(float(items[18]))
            rootData_RL3D.append(float(items[19]))
            rootData_RL4D.append(float(items[20]))
            rootData_RL5D.append(float(items[21]))
            rootData_RL6D.append(float(items[22]))
            rootData_RL7D.append(float(items[23]))
            rootData_RL8D.append(float(items[24]))
            rootData_RL9D.append(float(items[25]))
            # rootData_RL10D.append(float(items[27]))
    
    stackRange = range(int(rootData_Days[0]), int(rootData_Days[-1])+1)

    #REFERENCE FOR CODE TO DISPLAY GRAPH IN TEMPLATE: https://stackoverflow.com/questions/40534715/how-to-embed-matplotlib-graph-in-django-webpage
    fig, ax = plt.subplots()
    ax.stackplot(stackRange, rootData_RL1D, rootData_RL2D, rootData_RL3D, rootData_RL4D, rootData_RL5D, rootData_RL6D, rootData_RL7D, rootData_RL8D, rootData_RL9D, labels=['0-5cm', '5-15cm', '15-23cm', '23-38cm', '38-53cm', '53-61cm', '61-69cm', '69-84cm', '84-99cm'])
    ax.legend(loc='upper left')
    ax.set_xlabel('Days since planting')
    ax.set_ylabel('Soil Water')
    fig.suptitle('Soil Water by Layer', fontsize=16)
    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()
    return data


def plotOneAttribute(date, start_day, filename, attribute, yaxis, title):
    file = open(filename, 'r')
    text = file.readlines()
    file.close()

    day = int(date[len(date) - 3:])
    
    readingStress = False

    waterStress_Days = []
    waterStress_Values = []
    index = -1

    for line in text:
        items = list(filter(None, line.split(" ")))
        if len(items) == 0 and not readingStress:
            continue
        elif (readingStress and len(items) == 0) or (readingStress and int(items[1]) > day):
            break
        elif len(items) > 0 and not readingStress:
            if (items[0] == "@YEAR"):
                index = items.index(attribute)
                readingStress = True
        elif len(items) > 1 and readingStress and index > -1 and int(items[1]) >= int(start_day):
            adjusted_day = int(items[1]) - start_day
            waterStress_Days.append(int(adjusted_day))
            waterStress_Values.append(float(items[index]))
    
    stackRange = range(int(waterStress_Days[0]), int(waterStress_Days[-1])+1)

    #REFERENCE FOR CODE TO DISPLAY GRAPH IN TEMPLATE: https://stackoverflow.com/questions/40534715/how-to-embed-matplotlib-graph-in-django-webpage
    fig, ax = plt.subplots()
    ax.stackplot(stackRange, waterStress_Values, labels=[title])
    # ax.legend(loc='upper left')
    ax.set_xlabel('Days since planting')
    ax.set_ylabel(yaxis)
    fig.suptitle(title, fontsize=16)
    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()
    return data

def plotAquaSpy(date, start_day):
    day = int(date[len(date) - 3:])

    file = open("NE.SOL", 'r')
    text = file.readlines()
    file.close()

    rootDepth = getRootDepth(date) * 100

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
                readingSoil = True
        elif len(items) > 1 and readingSoil:
            soilArray.append(float(items[index]))
            if int(items[0]) > rootDepth:
                break

    file2 = open("UNLI2201.OSW", "r")
    text2 = file2.readlines()
    file2.close()

    readingWater = False
    index2 = -1
    waterArray = []

    for line in text2:
        currentArray = []
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
                for i in range(len(soilArray)):
                    currentArray.append(float(items[index2 + i]) / soilArray[i])
                waterArray.append(statistics.mean(currentArray) * 100)

    waterRange = range(1, len(waterArray)+1)

    fig, ax = plt.subplots()
    ax.stackplot(waterRange, waterArray, labels=["Soil Water"])
    # ax.legend(loc='upper left')
    ax.set_xlabel('Days since planting')
    ax.set_ylabel("Soil Water")
    fig.suptitle("Soil Water", fontsize=16)
    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    return data

def getRootDepth(date):
    file = open("UNLI2201.OPG", 'r')
    text = file.readlines()
    file.close()

    day = int(date[len(date) - 3:])
    reading = False

    for line in text:
        items = list(filter(None, line.split(" ")))
        if len(items) > 0 and items[0] == "@YEAR":
            reading = True
        elif reading == True and int(items[1]) == day:
            return float(items[33])
        
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

    commandFile = open("command.ps1", "w")
    commandFile.write("../../DSCSM048 %s A %s" % (hybrid, controlFile))
    commandFile.close()
        
    zip = zipfile.ZipFile("id-%s.zip" % (user_id), "w", zipfile.ZIP_DEFLATED)
    zip.write("command.ps1")
    zip.write("NE.SOL")
    zip.write("NENP2201.WTH")
    zip.write("UNLI2201.MZX")
    zip.close()

    s3 = boto3.client("s3", aws_access_key_id=env('AWS_ACCESS_KEY_ID'), aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'),)
    s3.upload_file("id-%s.zip" % (user_id), "vtapsbucket", "id-%s.zip" % (user_id))

    os.remove("id-%s.zip" % (user_id))
    os.remove("command.ps1")


    file_present = False

    bucket = None
    timeout = time.time() + 60*5

    while not file_present:
        bucket = s3.list_objects_v2(
            Bucket='outputvtapsbucket',
            Prefix ='id-%s/' % (user_id),
            MaxKeys=100 )
        
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

def createDirectory(user_id):
    if not os.path.isdir("id-%s" % (user_id)):
        os.mkdir("id-%s" % (user_id))
        shutil.copy2("UNLI2201.MZX", "id-%s/" % (user_id))
        shutil.copy2("NE.SOL", "id-%s/" % (user_id))
        shutil.copy2("NENP2201.WTH", "id-%s/" % (user_id))
