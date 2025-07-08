from django.shortcuts import render, redirect
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from main.models import User
from teacher.models import Teacher
from student.models import Student



def home(response):    
    user_id = response.session.get("user_id", None)
    if not user_id == None:
        return render(response, 'main/home.html', {"user_id": user_id})
    return render(response, 'main/home.html', {})

def reset(response):
    response.session.clear()
    Teacher.objects.all().delete()
    Student.objects.all().delete()

    non_superusers = User.objects.filter(is_superuser = False)
    non_superusers.delete()
    return redirect("/")