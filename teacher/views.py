from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import LoginTeacherForm, RegisterTeacherForm, SuperuserForm, WeekForm
from .models import Teacher, Game
from student.models import Student
from game.models import GameProfile
from main.models import User
from django.core import mail
from django.core.mail import EmailMultiAlternatives
import random
import string
import time
from django.http import HttpResponse    
import os
import io
from django.contrib.auth import get_user_model
from uuid import uuid4
import matplotlib.pyplot as plt

environment = os.environ['ENV']

def teacherHome(response):
    if response.user in User.objects.filter(is_superuser=True):
        form = SuperuserForm()
        if response.method == 'POST':
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
        try:
            teacher = user.teacher
        except:
            return redirect("/")
        user.games = [game for game in user.games if game is not None]
        user.save()
        userGames = []
        toDelete = []
        for index, game in enumerate(user.games):
            try:
                gameObject = Game.objects.get(id = game)
                userGames.append(gameObject)
            except:
                toDelete.append(index)
        for dIndex in reversed(toDelete):
            del user.games[dIndex]
        user.save()
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
    game.url = f"/teacher/game/{game.id}"
    teacher.games.append(game.id)

    while True:
        code = ''.join(random.choice(string.digits) for _ in range(4))
        if not Game.objects.filter(code=code).exists():
            game.code = code
            game.save()
            break
    
    
    teacher.save()

    return redirect(game.url)

def game(response, id):
    context = {}
    game = Game.objects.get(id = id)
    if game.created == False:
        if response.method == 'POST':
            players = []
            for player in response.POST['players'].split("\n"):
                player = player.replace("\r", "")
                players.append(player)
            game.players = players
            game.name = response.POST['gameName']
            game.created = True
            game.save()
            return redirect(f"/teacher/game/{game.id}")
        context = editGame(game)
        return render(response, 'game/newgame.html', context)
    elif game.passwordsFinished == False:
        context = passwordPage(game)
        game.passwordsFinished = True
        game.save()
        return render(response, 'game/password_page.html', context)
    else:
        if response.method == 'POST':
            week = response.POST['week']
            game.weekLimit = week
            game.save()
            return redirect(f"/teacher/game/{game.id}")
        context = gamePage(game)
        return render(response, 'game/student_page.html', context)


def editGame(game):
    context = {}

    game.name = "New Game"
    game.save()

    context['game'] = game
    return context


def passwordPage(game):
    context = {'players': [], "code": game.code, 'url': f'/teacher/game/{game.id}'}
    characters = string.ascii_letters + string.digits
    
    for player in game.players:
        if len(player) <= 0:
            continue
        
        player = player.strip()  
        newPassword = ''.join(random.choice(characters) for _ in range(6))

        try:
            student = Student.objects.get(username=player, code=game.code)
            user = student.user

            if student.tempPassword:
                user.set_password(newPassword)
                user.save(update_fields=['password'])
                context['players'].append({'username': student.username, 'password': newPassword})
            else:
                context['players'].append({'username': student.username, 'password': 'Already Created'})
        except:
            newUser = User.objects.create_user(username=uuid4().hex, password=newPassword)
            newUser.save()
            newPlayer = Student(username=player, code=game.code, user=newUser)
            newPlayer.game = game.id
            newPlayer.save()
            context['players'].append({'username': player, 'password': newPassword})

    game.passwordsFinished = True
    game.save()
    return context

def gamePage(game):
    context = {'players': [], 'code': game.code}
    studentList = []

    weekForm = WeekForm(initial = {'week': game.weekLimit})
    context['week_form'] = weekForm
    context['week_limit'] = game.weekLimit

    for player in game.players:
        playerInfo = {'username': player}
        student = Student.objects.get(username=player, code=game.code)
        try:
            gameProfile = GameProfile.objects.get(game=game, user=student.user)
            playerInfo['week'] = gameProfile.week
        except:
            playerInfo['week'] = 0
        
        studentList.append(student)
        context['players'].append(playerInfo)

    context['group_cost_graph'] = groupAttributeGraph(game, studentList, 'Cost')
    context['group_yield_graph'] = groupAttributeGraph(game, studentList, 'Yield')

    return context


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
        try:
            user = User.objects.get(email=player)
            student = user.student
            student.games.append(id)
            student.save()
            message = EmailMultiAlternatives("Hello from VTAPS!", "VTAPS Confirmation", "enersen1995@gmail.com", [player], connection=connection)
            message.attach_alternative(f"<p>Hello, {player}. Your teacher has added you to a VTAPS game.<br></br>Click <a href='{'http://localhost:8000' if environment == 'dev' else 'https://vtaps.org'}/student/login'> here</a> to login to VTAPS.org</p>", "text/html")
            message.send()
        except:
            user = User(email=player, username=player)
            user.set_unusable_password()
            user.save()
            student = Student(user=user)
            student.games.append(id)
            student.save()
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

def groupAttributeGraph(game, studentList, attribute):

    attributeNames = []
    attributeAmount = []

    for student in studentList:
        attributeNames.append(student.username)
        try:
            gameProfile = GameProfile.objects.get(user=student.user)
            if attribute == 'Cost':
                attributeAmount.append(gameProfile.total_cost)
            elif attribute == 'Yield':
                attributeAmount.append(gameProfile.projected_yields)
        except:
            attributeAmount.append(0)

    fig, ax = plt.subplots()


    if attribute == 'Cost':
        xlabel = 'Students'
        ylabel = 'Total Operational Costs'
        title = 'Cost Per Student'
        ax.bar(attributeNames, attributeAmount, color='skyblue')
        ax.set_ylim(bottom=750)
    elif attribute == 'Yield':
        xlabel = ''
        ylabel = 'Projected Yield'
        title = "Projected Yield Per Student"

        tickerLength = 0
        for layer in attributeAmount:  
            if layer == 0:
                continue    
            if len(layer) > tickerLength:
                tickerLength = len(layer)
            ax.plot(range(1, len(layer)+1, 1), layer)
        ax.set_xticks(range(1, tickerLength+1))    
        ax.legend(attributeNames, loc="upper left")
        ax.set_ylim(bottom=0)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    
    fig.suptitle(title, fontsize=16)
    
    imgdata = io.StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)
    data = imgdata.getvalue()

    plt.close(fig)
    
    return data