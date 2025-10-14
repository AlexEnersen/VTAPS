

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from .models import Student
from main.models import User
from teacher.models import Game
from .forms import LoginStudentForm, NewPasswordForm
import os

environment = os.environ['ENV']

def studentHome(response):
    if not response.user.is_authenticated:
        return redirect("/student/login")
    
    if response.user.student.tempPassword:
        if response.method == "POST":
            form = NewPasswordForm(response.POST)
            if not form.is_valid():
                return render(response, "student/s_newpassword.html", {"form": form})

            student = Student.objects.get(user=response.user)
            student.tempPassword = False
            student.save()

            # user = User.objects.get(id = response.user.id)
            # user.password = form.cleaned_data['password']
            # user.save()

            response.user.set_password(form.cleaned_data["password"])
            response.user.save()
            update_session_auth_hash(response, response.user)
            return redirect("/student")
        else:
            form = NewPasswordForm()
            
            return render(response, "student/s_newpassword.html", {"form": form})

    id = response.user.student.game

    # return render(response, "student/s_home.html", {"user": response.user, "student": response.user.student})
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