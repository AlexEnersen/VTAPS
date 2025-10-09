

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .models import Student
from teacher.models import Game
from .forms import LoginStudentForm
import os

environment = os.environ['ENV']

def studentHome(response):
    if not response.user.is_authenticated:
        return redirect("/student/login")

    id = response.user.student.game

    # return render(response, "student/s_home.html", {"user": response.user, "student": response.user.student, "game": game})
    return redirect(f'/game/{id}')

def studentLogin(response):
    if response.method == "POST":
        form = LoginStudentForm(request=response, data=response.POST)
        if form.is_valid():
            login(response, form.get_user())
            return redirect("/student")
    else:
        form = LoginStudentForm()
    return render(response, "student/s_login.html", {"form":form})

def studentLogout(response):
    logout(response)
    return redirect("/")