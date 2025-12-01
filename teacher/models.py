from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
import time

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

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    confirmed = models.BooleanField(default = False)        #Email Confirmed
    authorized = models.BooleanField(default = False)       #Authorized by superuser
    email = models.EmailField(max_length = 256, unique=True, blank=True, null=False)

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

class WeekEntries(models.Model):
    week = models.IntegerField("Week Limit", blank=False, choices=WEEK_CHOICES)