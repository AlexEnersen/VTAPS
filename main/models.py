from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    username = models.CharField(max_length = 128, blank=True, unique=True) ### Account Username
    hiddenName = models.CharField(max_length = 256, unique=False)          ### Student Username
    password = models.CharField(max_length = 256)
    email = models.EmailField(max_length = 256, unique=True, blank=True, null=False)


    games = ArrayField(models.CharField(max_length = 256), default=list, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

class Game(models.Model):
    name = models.CharField(max_length = 256, default=False)
    players = ArrayField(models.CharField(max_length = 256), default=list, blank=True)
    url = models.CharField(max_length = 256, default=False)