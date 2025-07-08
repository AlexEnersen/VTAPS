from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    email = models.EmailField(max_length = 256, unique=True)
    username = models.CharField(max_length = 16)
    password = models.CharField(max_length = 256)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['username']