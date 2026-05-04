from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
import time
from decimal import Decimal

WEEK_CHOICES = [
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6),
    (7, 7),
    (8, 8),
    (9, 9),
    (10, 10),
    (11, 11),
    (12, 12),
    (13, 13),
    (14, 14),
    (15, 15),
    (16, 16),
    (17, 17),
    (18, 18),
    (19, 19),
    (20, 20),
    (21, 'End')
]

N_COST_CHOICES = [
    (Decimal('0.50'), '$ 0.50'),
    (Decimal('0.55'), '$ 0.55'),
    (Decimal('0.60'), '$ 0.60'),
    (Decimal('0.65'), '$ 0.65'),
    (Decimal('0.70'), '$ 0.70'),
    (Decimal('0.75'), '$ 0.75'),
    (Decimal('0.80'), '$ 0.80'),
    (Decimal('0.85'), '$ 0.85'),
    (Decimal('0.90'), '$ 0.90'),
    (Decimal('0.95'), '$ 0.95'),
    (Decimal('1.00'), '$ 1.00'),
    (Decimal('1.05'), '$ 1.05'),
    (Decimal('1.10'), '$ 1.10'),
    (Decimal('1.15'), '$ 1.15'),
    (Decimal('1.20'), '$ 1.20'),
    (Decimal('1.25'), '$ 1.25'),
    (Decimal('1.30'), '$ 1.30'),
    (Decimal('1.35'), '$ 1.35'),
    (Decimal('1.40'), '$ 1.40'),
    (Decimal('1.45'), '$ 1.45'),
    (Decimal('1.50'), '$ 1.50')
]

I_COST_CHOICES = [
    (Decimal('5.0'), '$ 5.00'),
    (Decimal('5.5'), '$ 5.50'),
    (Decimal('6.0'), '$ 6.00'),
    (Decimal('6.5'), '$ 6.50'),
    (Decimal('7.0'), '$ 7.00'),
    (Decimal('7.5'), '$ 7.50'),
    (Decimal('8.0'), '$ 8.00'),
    (Decimal('8.5'), '$ 8.50'),
    (Decimal('9.0'), '$ 9.00'),
    (Decimal('9.5'), '$ 9.50'),
    (Decimal('10.0'), '$ 10.00'),
    (Decimal('10.5'), '$ 10.50'),
    (Decimal('11.0'), '$ 11.00'),
    (Decimal('11.5'), '$ 11.50'),
    (Decimal('12.0'), '$ 12.00'),
    (Decimal('12.5'), '$ 12.50'),
    (Decimal('13.0'), '$ 13.00'),
    (Decimal('13.5'), '$ 13.50'),
    (Decimal('14.0'), '$ 14.00'),
    (Decimal('14.5'), '$ 14.50'),
    (Decimal('15.0'), '$ 15.00')
]

CORN_PRICES = [
    (Decimal('3.5'), '$ 3.50'),
    (Decimal('3.6'), '$ 3.60'),
    (Decimal('3.7'), '$ 3.70'),
    (Decimal('3.8'), '$ 3.80'),
    (Decimal('3.9'), '$ 3.90'),
    (Decimal('4.0'), '$ 4.00'),
    (Decimal('4.1'), '$ 4.10'),
    (Decimal('4.2'), '$ 4.20'),
    (Decimal('4.3'), '$ 4.30'),
    (Decimal('4.4'), '$ 4.40'),
    (Decimal('4.5'), '$ 4.50'),
    (Decimal('4.6'), '$ 4.60'),
    (Decimal('4.7'), '$ 4.70'),
    (Decimal('4.8'), '$ 4.80'),
    (Decimal('4.9'), '$ 4.90'),
    (Decimal('5.0'), '$ 5.00'),
    (Decimal('5.1'), '$ 5.10'),
    (Decimal('5.2'), '$ 5.20'),
    (Decimal('5.3'), '$ 5.30'),
    (Decimal('5.4'), '$ 5.40'),
    (Decimal('5.5'), '$ 5.50'),
    (Decimal('5.6'), '$ 5.60'),
    (Decimal('5.7'), '$ 5.70'),
    (Decimal('5.8'), '$ 5.80'),
    (Decimal('5.9'), '$ 5.90'),
    (Decimal('6.0'), '$ 6.00'),
    (Decimal('6.1'), '$ 6.10'),
    (Decimal('6.2'), '$ 6.20'),
    (Decimal('6.3'), '$ 6.30'),
    (Decimal('6.4'), '$ 6.40'),
    (Decimal('6.5'), '$ 6.50'),
    (Decimal('6.6'), '$ 6.60'),
    (Decimal('6.7'), '$ 6.70'),
    (Decimal('6.8'), '$ 6.80'),
    (Decimal('6.9'), '$ 6.90'),
    (Decimal('7.0'), '$ 7.00'),
    (Decimal('7.1'), '$ 7.10'),
    (Decimal('7.2'), '$ 7.20'),
    (Decimal('7.3'), '$ 7.30'),
    (Decimal('7.4'), '$ 7.40'),
    (Decimal('7.5'), '$ 7.50')
]

WATER_N_CHOICES = [
    (Decimal('1'), '1.00'),
    (Decimal('2'), '2.00'),
    (Decimal('3'), '3.00'),
    (Decimal('4'), '4.00'),
    (Decimal('5'), '5.00'),
    (Decimal('6'), '6.00'),
    (Decimal('7'), '7.00'),
    (Decimal('8'), '8.00'),
    (Decimal('9'), '9.00'),
    (Decimal('10'), '10.00'),
    (Decimal('11'), '11.00'),
    (Decimal('12'), '12.00'),
    (Decimal('13'), '13.00'),
    (Decimal('14'), '14.00'),
    (Decimal('15'), '15.00'),
    (Decimal('16'), '16.00'),
    (Decimal('17'), '17.00'),
    (Decimal('18'), '18.00'),
    (Decimal('19'), '19.00'),
    (Decimal('20'), '20.00'),
    (Decimal('21'), '21.00'),
    (Decimal('22'), '22.00'),
    (Decimal('23'), '23.00'),
    (Decimal('24'), '24.00'),
    (Decimal('25'), '25.00'),
    (Decimal('26'), '26.00'),
    (Decimal('27'), '27.00'),
    (Decimal('28'), '28.00'),
    (Decimal('29'), '29.00'),
    (Decimal('30'), '30.00'),
    (Decimal('31'), '31.00'),
    (Decimal('32'), '32.00'),
    (Decimal('33'), '33.00'),
    (Decimal('34'), '34.00'),
    (Decimal('35'), '35.00'),
    (Decimal('36'), '36.00'),
    (Decimal('37'), '37.00'),
    (Decimal('38'), '38.00'),
    (Decimal('39'), '39.00'),
    (Decimal('40'), '40.00'),
    (Decimal('39'), '39.00'),
    (Decimal('40'), '40.00'),
    (Decimal('39'), '39.00'),
    (Decimal('40'), '40.00'),
    (Decimal('39'), '39.00'),
    (Decimal('40'), '40.00'),
    (Decimal('41'), '41.00'),
    (Decimal('42'), '42.00'),
    (Decimal('43'), '43.00'),
    (Decimal('44'), '44.00'),
    (Decimal('45'), '45.00'),
    (Decimal('46'), '46.00'),
    (Decimal('47'), '47.00'),
    (Decimal('48'), '48.00'),
    (Decimal('49'), '49.00'),
    (Decimal('50'), '50.00'),
]

WEATHER_CHOICES = [
    ("Random", "Random Weather"),
    ("NEME0401.WTH", '2004'),
    ("NEME0501.WTH", '2005'),
    ("NEME0601.WTH", '2006'),
    ("NEME0701.WTH", '2007'),
    ("NEME0801.WTH", '2008'),
    ("NEME0901.WTH", '2009'),
    ("NEME1001.WTH", '2010'),
    ("NEME1101.WTH", '2011'),
    ("NEME1201.WTH", '2012'),
    ("NEME1301.WTH", '2013'),
    ("NEME1401.WTH", '2014'),
    ("NEME1501.WTH", '2015'),
    ("NEME1601.WTH", '2016'),
    ("NEME1701.WTH", '2017'),
    ("NEME1801.WTH", '2018'),
    ("NEME1901.WTH", '2019'),
    ("NEME2001.WTH", '2020'),
    ("NEME2101.WTH", '2021'),
    ("NEME2201.WTH", '2022'),
    ("NEME2301.WTH", '2023'),
    ("NEME2401.WTH", '2024'),
]

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    confirmed = models.BooleanField(default = False)        #Email Confirmed
    authorized = models.BooleanField(default = False)       #Authorized by superuser
    email = models.EmailField(max_length = 256, unique=True, blank=True, null=True)

    games = ArrayField(models.CharField(max_length = 256), default=list, blank=True)

    activation_key = models.CharField(max_length=40, default=None, null=True, unique=True)
    key_expires = models.IntegerField(default=time.time, blank=True)

class Game(models.Model):
    name = models.CharField(max_length = 256, default=False)
    players = ArrayField(models.CharField(max_length = 256), default=list, blank=True)
    url = models.CharField(max_length = 256, default=False)

    weekLimit = models.IntegerField(default = 6)

    code = models.CharField(blank=True)
    created = models.BooleanField(default = False)
    passwordsFinished = models.BooleanField(default = False)
    
    nitrogenCost = models.FloatField(default=0.6)
    irrigationCost = models.FloatField(default=6.50)
    waterNitrates = models.FloatField(default=25.0)
    cornPrice = models.FloatField(default=4.25)
    otherCosts = models.DecimalField(default=742.79, decimal_places=2, max_digits=6)
    weatherFile = models.CharField(default="NEME2101.WTH")

class WeekEntries(models.Model):
    week = models.IntegerField("Week Limit", blank=False, choices=WEEK_CHOICES)

class GameSetup(models.Model):
    nitrogenCost = models.DecimalField("Fertilizer Cost (per lb.)", choices=N_COST_CHOICES, default = Decimal('0.6'), max_digits = 4, decimal_places = 2)
    irrigationCost = models.DecimalField("Irrigation Cost (per in.)", choices=I_COST_CHOICES, default = Decimal('6.50'), max_digits = 4, decimal_places = 2)
    waterNitrates = models.DecimalField("Water Nitrates (ppm per in.)", choices=WATER_N_CHOICES, default = Decimal('25.0'), max_digits = 4, decimal_places = 2)
    cornPrice = models.DecimalField("Corn Price:", choices=CORN_PRICES, default = Decimal('4.25'), max_digits = 4, decimal_places = 2)
    otherCosts = models.DecimalField(default=742.79, decimal_places=2, max_digits=6)
    weatherFile = models.CharField("North Platte Weather:", choices=WEATHER_CHOICES, default="NEME2101.WTH", max_length=40)