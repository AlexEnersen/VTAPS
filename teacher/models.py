from django.db import models
from django.contrib.auth.models import AbstractUser

class Teacher(AbstractUser):
    email = models.EmailField(max_length = 256, unique=True)
    username = models.CharField(max_length = 16)
    password = models.CharField(max_length = 256)
    accepted = models.BooleanField(default = False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
