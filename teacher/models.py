from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
import time

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    confirmed = models.BooleanField(default = False)        #Email Confirmed
    authorized = models.BooleanField(default = False)       #Authorized by superuser

    games = ArrayField(models.CharField(max_length = 256), default=list, blank=True)

    activation_key = models.CharField(max_length=40, default=None, null=True, unique=True)
    key_expires = models.IntegerField(default=time.time, blank=True)

class Game(models.Model):
    name = models.CharField(max_length = 256, default=False)
    players = ArrayField(models.CharField(max_length = 256), default=list, blank=True)
    url = models.CharField(max_length = 256, default=False)
    url2 = models.CharField(max_length = 256, default=False)
    created = models.BooleanField(default = False)