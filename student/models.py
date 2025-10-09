from django.db import models
from django.contrib.postgres.fields import ArrayField
import time

from django.conf import settings

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    username = models.CharField(max_length = 64, blank=False)
    code = models.CharField(max_length=16, blank=False)

    game = models.CharField(max_length = 256, default=list, blank=True)