from django.shortcuts import render, redirect
# from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model

def home(response):
    print(get_user_model().objects.all())
    
    get_user_model().objects.all().delete()
    # response.session.clear()
    # Session.objects.all().delete()
    user_id = response.session.get("user_id", None)
    if not user_id == None:
        return render(response, 'main/home.html', {"user_id": user_id})
    return render(response, 'main/home.html', {})

def reset(response):
    response.session.clear()
    # Session.objects.all().delete()
    return redirect("/")