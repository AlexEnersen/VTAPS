from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import LoginTeacherForm, RegisterTeacherForm
from .models import Teacher
from django.core import mail
from django.core.mail import EmailMultiAlternatives
import random
import string
import time
from django.http import HttpResponse    
import os

environment = os.environ['ENV']

def teacherHome(response):
    if not response.user.is_authenticated:
        return render(response, "teacher/t_home.html", {"user": None, "authenticated": None})
    else:
        return render(response, "teacher/t_home.html", {"user": response.user, "authenticated": response.user.is_authenticated})

def teacherRegister(response):
    if response.method == "POST":
        form = RegisterTeacherForm(response.POST)
        if form.is_valid():
            user = form.save()

            sendConfirmationEmail(user)
            return render(response, "teacher/t_submission.html")
        else:
            return render(response, "error_register.html")
    else:
        form = RegisterTeacherForm()
    return render(response, "teacher/t_register.html", {"form":form})

def teacherLogin(response):
    if response.method == "POST":
        form = LoginTeacherForm(response.POST)
        username = response.POST['username']
        password = response.POST['password']
        user = authenticate(response, username=username, password=password)
        print(user)
        if user is not None:
            login(response, user)

        return redirect("/teacher")
    else:
        form = LoginTeacherForm()
    return render(response, "teacher/t_login.html", {"form":form})

def teacherConfirm(response, activation_key):
    try:
        teacher = Teacher.objects.get(activation_key=activation_key)
        if teacher.key_expires > time.time():
            teacher.confirmed = True
            teacher.save()
            return render(response, "teacher/t_confirmation.html")
        else:
            return render(response, 'teacher/t_failure.html')
    except:
        return render(response, 'teacher/t_failure.html')

def teacherLogout(response):
    logout(response)
    return redirect("/teacher")

def teacherSendEmail(response):
    sendConfirmationEmail(response.user)
    return redirect("/teacher")

def sendConfirmationEmail(user):
    try:
        while(1):
            activation_key = "".join(random.sample(string.ascii_uppercase, 10))
            print(activation_key)
            Teacher.objects.get(activation_key=activation_key)
    except:
        user.activation_key = activation_key
        user.key_expires = time.time() + (60 * 60 * 24 * 7)
        user.save()

        connection = mail.get_connection()
        connection.open()

        message = EmailMultiAlternatives("Hello from Django", "This is a test", "enersen1995@gmail.com", [user], connection=connection)
        message.attach_alternative(f"<p>Hello {user.username}. This is a confirmation email for VTAPS.org. If you did not create an account recently, please disregard this message</br></br>Click <a href='{'http://localhost:8000' if environment == 'dev' else 'https://vtaps.org'}/teacher/confirm/{activation_key}'/> here</a> to finalize your registration with VTAPS.org</p>", "text/html")
        message.send()

        connection.close()

