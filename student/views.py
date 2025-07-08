

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .models import Student
from .forms import LoginStudentForm, RegisterStudentForm
from django.core import mail
from django.core.mail import EmailMultiAlternatives
import random
import string
import time
from django.http import HttpResponse    
import os

environment = os.environ['ENV']

def studentHome(response):
    print("STUDENT")
    # print(response.method)
    # if response.user.is_superuser:
    #     form = SuperuserForm()
    #     if response.method == 'POST':
    #         user = get_user_model().objects.get(email = response.POST['email'])
    #         print(user)
    #         user.authorized = True
    #         user.save()

    #     unauthorized_users = get_user_model().objects.filter(is_superuser = False, confirmed = True, authorized = False)
    #     authorized_users = get_user_model().objects.filter(is_superuser = False, confirmed = True, authorized = True)

    #     context = {"unauthorized_users": unauthorized_users, "authorized_users": authorized_users, "form": form}
    #     return render(response, "teacher/t_admin.html", context)
    # elif not response.user.is_authenticated:
    #     return render(response, "teacher/t_home.html", {"user": None, "authenticated": None})
    # else:
    #     user = response.user
    #     print(user.games)
    #     user.games = [game for game in user.games if game is not None]
    #     user.save()
    #     userGames = []
    #     for game in user.games:
    #         print(game)
    #         if game == None:
    #             game.delete()
    #         else:
    #             userGames.append(Game.objects.get(id = game))
    return render(response, "student/s_home.html", {})

def studentRegister(response):
    if response.method == "POST":
        form = RegisterStudentForm(response.POST)
        if form.is_valid():
            user = form.save()

            sendConfirmationEmail(user)
            return render(response, "student/s_submission.html")
        else:
            return render(response, "error_register.html")
    else:
        form = RegisterStudentForm()
    return render(response, "student/s_register.html", {"form":form})

def studentLogin(response):
    if response.method == "POST":
        form = LoginStudentForm(response.POST)
        username = response.POST['username']
        password = response.POST['password']
        user = authenticate(response, username=username, password=password)
        print(user)
        if user is not None:
            login(response, user)

        return redirect("/student")
    else:
        form = LoginStudentForm()
    return render(response, "student/s_login.html", {"form":form})

def studentLogout(response):
    logout(response)
    return redirect("/student")

def studentConfirm(response, activation_key):
    try:
        student = Student.objects.get(activation_key=activation_key)
        if student.key_expires > time.time():
            student.confirmed = True
            student.save()
            if student.user.password == None:
                return render(response, "student/s_setpassword.html")
            else:
                return render(response, "student/s_confirmation.html")
        else:
            return render(response, 'student/s_failure.html')
    except:
        return render(response, 'student/s_failure.html')