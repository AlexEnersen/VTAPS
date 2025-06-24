from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
import time

class Teacher(AbstractUser):
    email = models.EmailField(max_length = 256, unique=True)
    username = models.CharField(max_length = 16)
    password = models.CharField(max_length = 256)
    confirmed = models.BooleanField(default = False)        #If this gets removed, you can't create super users anymore
    authorized = models.BooleanField(default = False)

    games = ArrayField(models.CharField(max_length = 256), default=list, blank=True)

    activation_key = models.CharField(max_length=40, default=None, null=True, unique=True)
    key_expires = models.IntegerField(default=time.time, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Game(models.Model):
    name = models.CharField(max_length = 256, default=False)
    players = ArrayField(models.CharField(max_length = 256), default=list, blank=True)
    url = models.CharField(max_length = 256, default=False)