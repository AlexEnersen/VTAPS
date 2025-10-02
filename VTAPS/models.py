from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField

class User(AbstractUser):
    username = models.CharField(max_length = 16)
    password = models.CharField(max_length = 256, null=True, default=None)
    
    email = models.EmailField(max_length = 256, unique=False, blank=True, null=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['username']