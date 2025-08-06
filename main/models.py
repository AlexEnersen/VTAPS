from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    email = models.EmailField(max_length = 256, unique=True)
    username = models.CharField(max_length = 256)
    password = models.CharField(max_length = 256)

    games = ArrayField(models.CharField(max_length = 256), default=list, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Game(models.Model):
    name = models.CharField(max_length = 256, default=False)
    players = ArrayField(models.CharField(max_length = 256), default=list, blank=True)
    url = models.CharField(max_length = 256, default=False)