from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from teacher.models import Game

HYBRID_CHOICES = [
    ('IB2074 Channel213-19VTPRIB', 'Channel213-19VTPRIB ($270/bag)'),
    ('IB2075 Fontanelle 11D637', 'Fontanelle 11D637 ($262/bag)'),
    ('IB2073 Pioneer 0801AM', 'Pioneer 0801AM ($225/bag)'),
    ('IB2072 Pioneer 1197AM', 'Pioneer 1197AM ($235/bag)'),
    ('IB1071 Pioneer 1366AML', 'Pioneer 1366AML ($243/bag)'),
    ('IB1073 Pioneer 1185', 'Pioneer 1185AM ($260/bag)')
]

SEEDING_CHOICES = [
    (24000, 24000),
    (24500, 24500),
    (25000, 25000),
    (25500, 25500),
    (26000, 26000),
    (26500, 26500),
    (27000, 27000),
    (27500, 27500),
    (28000, 28000),
    (28500, 28500),
    (29000, 29000),
    (29500, 29500),
    (30000, 30000),
    (30500, 30500),
    (31000, 31000),
    (31500, 31500),
    (32000, 32000),
    (32500, 32500),
    (33000, 33000),
    (33500, 33500),
    (34000, 34000),
    (34500, 34500),
    (35000, 35000),
    (35500, 35500),
    (36000, 36000),
    (36500, 36500),
    (37000, 37000),
    (37500, 37500),
    (38000, 38000),
    (38500, 38500),
    (39000, 39000),
    (39500, 39500),
    (40000, 40000),
    (40500, 40500),
    (41000, 41000),
    (41500, 41500),
    (42000, 42000)
]

IRRIGATION_CHOICES = [
    (0, 0),
    (0.10, 0.10),
    (0.20, 0.20),
    (0.30, 0.30),
    (0.40, 0.40),
    (0.50, 0.50),
    (0.60, 0.60),
    (0.70, 0.70),
    (0.80, 0.80),
    (0.90, 0.90),
    (1, 1),
]

FERT_CHOICES_1 = [
    (0, 0),
    (5, 5),
    (10, 10),
    (15, 15),
    (20, 20),
    (25, 25),
    (30, 30),
    (35, 35),
    (40, 40),
    (45, 45),
    (50, 50),
    (55, 55),
    (60, 60),
    (65, 65),
    (70, 70),
    (75, 75),
    (80, 80),
    (85, 85),
    (90, 90),
    (95, 95),
    (100, 100),
    (105, 105),
    (110, 110),
    (115, 115),
    (120, 120),
    (125, 125),
    (130, 130),
    (135, 135),
    (140, 140),
    (145, 145),
    (150, 150),
    (155, 155),
    (160, 160),
    (165, 165),
    (170, 170),
    (175, 175),
    (180, 180)
]

FERT_CHOICES_2 = [
    (0, 0),
    (5, 5),
    (10, 10),
    (15, 15),
    (20, 20),
    (25, 25),
    (30, 30)
]

class GameProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    hybrid = models.CharField(max_length=30, choices=HYBRID_CHOICES, null=True, default=None)
    seeding_rate = models.IntegerField(choices=SEEDING_CHOICES, default=10000)
    week = models.IntegerField(default=0)
    fert_id = models.IntegerField(default=-1, blank=False)
    initialized = models.BooleanField(default=False)
    computing = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    
    projected_yields = ArrayField(models.FloatField(default=0), default=list, blank=True)
    monday_irrigation = ArrayField(models.FloatField(default=0), default=list, blank=True)
    thursday_irrigation = ArrayField(models.FloatField(default=0), default=list, blank=True)
    weekly_fertilizer = ArrayField(models.FloatField(default=0), default=list, blank=True)
    fertigation = ArrayField(models.FloatField(default=0), default=list, blank=True)

    total_cost = models.FloatField(default=0)
    agronomic_efficiency = models.FloatField(default=0)
    irrigation_water_use_efficiency = models.FloatField(default=0)
    nitrogen_leaching = models.FloatField(default=0)
    nitrogen_leaching_array = ArrayField(models.FloatField(default=0), default=list, blank=True)
    nitrogen_uptake = models.FloatField(default=0)
    nitrogen_sufficiency_array = ArrayField(models.FloatField(default=0), default=list, blank=True)
    nitrogen_sufficiency = models.FloatField(default=0)
    wnipi = models.FloatField(default=0)
    
    partialFactorProductivity = models.FloatField(default=-1)
    nitrogenUseEfficiency = models.FloatField(default=-1)
    waterUseEfficiency = models.FloatField(default=-1)
    waterProductivity = models.FloatField(default=-1)

    waterLimit = models.CharField(default="unlimited")

    yield_vs_et = models.FloatField(default=-1)

    profit = models.FloatField(default=0)
    
class FertilizerEntries1(models.Model):
    fertilizer = models.IntegerField(blank=False, default=0, choices=FERT_CHOICES_1)

class FertilizerEntries2(models.Model):
    fertilizer = models.IntegerField(blank=False, default=0, choices=FERT_CHOICES_2)

class IrrigationEntries(models.Model):
    monday = models.FloatField(choices=IRRIGATION_CHOICES, default=0)
    thursday = models.FloatField(choices=IRRIGATION_CHOICES, default=0)

class FertilizerInit(models.Model):
    week1 = models.IntegerField("Week 1, At-plant Nitrogen", blank=False, default=0, choices=FERT_CHOICES_1)
    week6 = models.IntegerField("Week 6, Side-Dress Nitrogen", blank=False, default=0, choices=FERT_CHOICES_1)
    week9 = models.IntegerField("Week 9, V9 Fertigation Nitrogen", blank=False, default=0, choices=FERT_CHOICES_2)
    week10 = models.IntegerField("Week 10, V12 Fertigation Nitrogen", blank=False, default=0, choices=FERT_CHOICES_2)
    week12 = models.IntegerField("Week 12, VT Fertigation Nitrogen", blank=False, default=0, choices=FERT_CHOICES_2)
    week14 = models.IntegerField("Week 14, R2 Fertigation Nitrogen", blank=False, default=0, choices=FERT_CHOICES_2)
    week15 = models.IntegerField("Week 15, R3 Fertigation Nitrogen", blank=False, default=0, choices=FERT_CHOICES_2)

    