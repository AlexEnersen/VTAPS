from django.db import models
from django.core.validators import MinValueValidator

HYBRID_CHOICES = [
    ('MZCER048', 'MZCER048')
    # ('BRPI0202', 'BRPI0202'),
    # ('EBPL8501', 'EBPL8501'),
    # ('FLSC8101', 'FLSC8101'),
    # ('GAGR0201', 'GAGR0201'),
    # ('GHWA0401', 'GHWA0401'),
    # ('IBWA8301', 'IBWA8301'),
    # ('IUAF9901', 'IUAF9901'),
    # ('SIAZ9601', 'SIAZ9601'),
    # ('UFGA8201', 'UFGA8201')
]

SEEDING_CHOICES = [
    (24000, 24000),
    (26000, 26000),
    (28000, 28000),
    (30000, 30000),
    (32000, 32000),
    (34000, 34000),
    (36000, 36000),
    (38000, 38000),
    (40000, 40000),
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

WEATHER_CHOICES = [
    ('Normal', 'Normal'),
    ('Wet', 'Wet'),
    ('Dry', 'Dry')
]

class SingleplayerProfile(models.Model):
    hybrid = models.CharField(max_length=8, choices=HYBRID_CHOICES, default="BRPI0202")
    seeding_rate = models.IntegerField(choices=SEEDING_CHOICES, default=10000)
    weather_type = models.CharField(max_length=6, choices=WEATHER_CHOICES, default='Normal')
    week = models.IntegerField(default=1)
    fert_id = models.IntegerField(default=-1, blank=False)

class FertilizerEntries1(models.Model):
    fertilizer = models.IntegerField(blank=False, default=0, choices=FERT_CHOICES_1)

class FertilizerEntries2(models.Model):
    fertilizer = models.IntegerField(blank=False, default=0, choices=FERT_CHOICES_2)

class IrrigationEntries(models.Model):
    monday = models.FloatField(choices=IRRIGATION_CHOICES, default=0)
    thursday = models.FloatField(choices=IRRIGATION_CHOICES, default=0)

class FertilizerInit(models.Model):
    week1 = models.IntegerField("Pre-plant Nitrogen, Week 1 (lbs/acre)", blank=False, default=0, choices=FERT_CHOICES_1)
    week6 = models.IntegerField("Side-Dress Nitrogen, Week 6 (lbs/acre)", blank=False, default=0, choices=FERT_CHOICES_1)
    week9 = models.IntegerField("V9 Fertigation Nitrogen, Week 9 (lbs/acre)", blank=False, default=0, choices=FERT_CHOICES_2)
    week10 = models.IntegerField("V12 Fertigation Nitrogen, Week 10 (lbs/acre)", blank=False, default=0, choices=FERT_CHOICES_2)
    week12 = models.IntegerField("VT Fertigation Nitrogen, Week 12 (lbs/acre)", blank=False, default=0, choices=FERT_CHOICES_2)
    week14 = models.IntegerField("R2 Fertigation Nitrogen, Week 14 (lbs/acre)", blank=False, default=0, choices=FERT_CHOICES_2)
    week15 = models.IntegerField("R3 Fertigation Nitrogen, Week 15 (lbs/acre)", blank=False, default=0, choices=FERT_CHOICES_2)

    