from django.shortcuts import render, redirect
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from main.models import User
from teacher.models import Teacher
from student.models import Student
from game.models import GameProfile



def home(response):    
    game_id = response.session.get("game_id", None)
    print("user:", hasattr(response.user, "teacher")) 
    print("user:", hasattr(response.user, "student")) 
    if hasattr(response.user, "student"):
        return redirect('/student')
    elif hasattr(response.user, "teacher"):
        return redirect("/teacher")
    else:
        return render(response, 'main/home.html', {"game_id": game_id})

def reset(response):
    game_id = response.session.get("game_id", None)
    currentGames = GameProfile.objects.filter(id = game_id)
    currentGames.delete()
    if game_id:
        del response.session['game_id']
    # Teacher.objects.all().delete()
    # Student.objects.all().delete()
    # GameProfile.objects.all().delete()

    # print(User.objects.filter(is_superuser = False, teacher__isnull = True))

    # non_superusers = User.objects.filter(is_superuser = False, teacher__isnull = True   )
    # non_superusers.delete()
    return redirect("/")