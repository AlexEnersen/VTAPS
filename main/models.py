from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    username = models.CharField(max_length = 128, blank=True, unique=True) ### Account Username
    # password = models.CharField(max_length = 256)


    games = ArrayField(models.CharField(max_length = 256), default=list, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

class Game(models.Model):
    name = models.CharField(max_length = 256, default=False)
    players = ArrayField(models.CharField(max_length = 256), default=list, blank=True)
    url = models.CharField(max_length = 256, default=False)