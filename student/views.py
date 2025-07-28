

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .models import Student
from .forms import LoginStudentForm, ConfirmStudentForm
from django.core import mail
from django.core.mail import EmailMultiAlternatives
import random
import string
import time
from django.http import HttpResponse    
import os

environment = os.environ['ENV']

def studentHome(response):
    if not response.user.is_authenticated:
        return redirect("/student/login")

    return render(response, "student/s_home.html", {"user": response.user, "student": response.user.student})

def studentLogin(response):
    if response.method == "POST":
        form = LoginStudentForm(response.POST)
        username = response.POST['username']
        password = response.POST['password']
        user = authenticate(response, username=username, password=password)
        if user is not None:
            login(response, user)

        return redirect("/student")
    else:
        form = LoginStudentForm()
    return render(response, "student/s_login.html", {"form":form})

def studentLogout(response):
    logout(response)
    return redirect("/")

def studentConfirm(response, activation_key):
    student = Student.objects.get(activation_key=activation_key)
    user = student.user
    if response.method == 'POST':
        form = ConfirmStudentForm(response.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            student.confirmed = True
            student.save()
            return redirect('/student/login')
    else:
        try:
            if student.key_expires > time.time():
                print("User password:", user.password)
                if user.has_usable_password() is False:
                    form = ConfirmStudentForm()
                    context = {"form": form}
                    return render(response, "student/s_setpassword.html", context)
                else:
                    return render(response, "student/s_confirmation.html")
            else:
                return render(response, 'student/s_failure.html')
        except:
            return render(response, 'student/s_failure.html')