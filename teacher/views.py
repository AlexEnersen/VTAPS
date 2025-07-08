from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import LoginTeacherForm, RegisterTeacherForm, SuperuserForm
from .models import Teacher, Game
from student.models import Student
from main.models import User
from django.core import mail
from django.core.mail import EmailMultiAlternatives
import random
import string
import time
from django.http import HttpResponse    
import os
from django.contrib.auth import get_user_model

environment = os.environ['ENV']

def teacherHome(response):
    if response.user in User.objects.filter(is_superuser=True):
        form = SuperuserForm()
        if response.method == 'POST':
            print("EMAIL:", response.POST['email'])
            user = User.objects.get(email = response.POST['email'])
            teacher = user.teacher
            teacher.authorized = True
            teacher.save()

        unauthorized_users = Teacher.objects.filter(confirmed = True, authorized = False)
        authorized_users = Teacher.objects.filter(confirmed = True, authorized = True)

        context = {"unauthorized_users": unauthorized_users, "authorized_users": authorized_users, "form": form}
        return render(response, "teacher/t_admin.html", context)
    elif not response.user.is_authenticated:
        return render(response, "teacher/t_home.html", {"user": None, "authenticated": None})
    else:
        user = response.user
        teacher = user.teacher
        user.games = [game for game in user.games if game is not None]
        user.save()
        userGames = []
        for game in user.games:
            if game == None:
                game.delete()
            else:
                userGames.append(Game.objects.get(id = game))
        print(teacher.confirmed)
        return render(response, "teacher/t_home.html", {"user": user, "games": userGames})

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
        if user is not None:
            login(response, user)

        return redirect("/teacher")
    else:
        form = LoginTeacherForm()
    return render(response, "teacher/t_login.html", {"form":form})

def teacherLogout(response):
    logout(response)
    return redirect("/teacher")

def teacherSendEmail(response):
    sendConfirmationEmail(response.user)
    return redirect("/teacher")

def newGame(response):
    teacher = response.user

    game = Game()
    game.save()
    teacher.games.append(game.id)
    
    
    game.url = f"/teacher/editGame/{game.id}/"
    game.url2 = f"/teacher/createGame/{game.id}/"
    game.save()

    teacher.save()

    return redirect(game.url)

def editGame(response, id):
    game = Game.objects.get(id = id)
    if response.method == 'POST':
        addedPlayers = response.POST['players'].split("\n")
        for player in addedPlayers:
            game.players.append(player)
    
    game.save()

    return render(response, 'game/newgame.html', {"game": game})

def sendConfirmationEmail(user):
    try:
        while(1):
            activation_key = "".join(random.sample(string.ascii_uppercase, 10))
            Teacher.objects.get(activation_key=activation_key)
    except:
        teacher = user.teacher
        teacher.activation_key = activation_key
        teacher.key_expires = time.time() + (60 * 60 * 24 * 7)
        teacher.save()

        connection = mail.get_connection()
        connection.open()

        message = EmailMultiAlternatives("Hello from VTAPS!", "VTAPS Confirmation", "enersen1995@gmail.com", [user.email], connection=connection)
        message.attach_alternative(f"<p>Hello, {user.username}. This is a confirmation email for VTAPS.org. If you did not create an account recently, please disregard this message</br></br>Click <a href='{'http://localhost:8000' if environment == 'dev' else 'https://vtaps.org'}/teacher/confirm/{activation_key}'> here</a> to finalize your registration with VTAPS.org</p>", "text/html")
        message.send()

        connection.close()

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
    
def createGame(response, id):
    game = Game.objects.get(id=id)
    game.confirmed = True
    game.save()

    for player in game.players:
        connection = mail.get_connection()
        connection.open()
        user = User(email=player, username=player)
        user.save()
        student = Student(user=user)
        try:
            while(1):
                activation_key = "".join(random.sample(string.ascii_uppercase, 10))
                Teacher.objects.get(activation_key=activation_key)
        except:
            student.activation_key = activation_key
            student.key_expires = time.time() + (60 * 60 * 24 * 7)
            student.save()
            message = EmailMultiAlternatives("Hello from VTAPS!", "VTAPS Confirmation", "enersen1995@gmail.com", [player], connection=connection)
            message.attach_alternative(f"<p>Hello, {player}. Your teacher has added you to a VTAPS game.<br></br>Click <a href='{'http://localhost:8000' if environment == 'dev' else 'https://vtaps.org'}/student/confirm/{activation_key}'> here</a> to make an account with VTAPS.org</p>", "text/html")
            message.send()

            connection.close()


    return redirect('/teacher')