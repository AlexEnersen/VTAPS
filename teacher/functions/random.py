import os
import watchtower, logging
import numpy as np

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