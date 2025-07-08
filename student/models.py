from django.db import models
from django.contrib.postgres.fields import ArrayField
import time

from django.conf import settings

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    confirmed = models.BooleanField(default = False)        #Email Confirmed

    activation_key = models.CharField(max_length=40, default=None, null=True, unique=True)
    key_expires = models.IntegerField(default=time.time, blank=True)