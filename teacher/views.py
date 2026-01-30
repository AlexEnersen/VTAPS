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
from uuid import uuid4
import matplotlib.pyplot as plt
import csv
import environ
import watchtower, logging
import boto3
from django.http import HttpResponseRedirect
from botocore.config import Config
environment = os.environ['ENV']

secret_name = "S3_Keys"
region_name = "us-east-1"

if environment == 'prod':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(watchtower.CloudWatchLogHandler())

try:
    if environment == 'prod':
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        SECRET_KEY = eval(get_secret_value_response['SecretString'])
        s3_access_key = SECRET_KEY['S3_ACCESS_KEY_ID']
        s3_secret_key = SECRET_KEY['S3_SECRET_ACCESS_KEY']
        
    else:
        env = environ.Env()
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
        s3_access_key = env('S3_ACCESS_KEY_ID')
        s3_secret_key = env('S3_SECRET_ACCESS_KEY')

    client_config = Config(
        max_pool_connections=100
    )

    s3 = boto3.client("s3", aws_access_key_id=s3_access_key, aws_secret_access_key=s3_secret_key, config=client_config)
        
except Exception as error:
    if environment == 'prod':
        logger.info('error:', error)
    else:
        print('Error:', error)

def teacherHome(response):
    if response.user in User.objects.filter(is_superuser=True):
        form = SuperuserForm()
        if response.method == 'POST':
            user = User.objects.get(email = response.POST['email'])
            teacher = user.teacher
            teacher.confirmed = True
            teacher.authorized = True
            teacher.save()

        unconfirmed_users = Teacher.objects.filter(confirmed = False, authorized = False)
        unauthorized_users = Teacher.objects.filter(confirmed = True, authorized = False)
        authorized_users = Teacher.objects.filter(confirmed = True, authorized = True)

        context = {"unauthorized_users": unauthorized_users, "authorized_users": authorized_users, "unconfirmed_users": unconfirmed_users, "form": form}
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

            # sendConfirmationEmail(user)
            return render(response, "teacher/t_submission.html")
        else:
            return render(response, "error_register.html")
    else:
        form = RegisterTeacherForm()
    return render(response, "teacher/t_register.html", {"form":form})

def teacherLogin(response):
    if response.method == "POST":
        form = LoginTeacherForm(request=response, data=response.POST)
        if form.is_valid():
            login(response, form.get_user())
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
    try:
        game = Game.objects.get(id = id)
    except:
        return redirect("/teacher")
    if not response.user.is_authenticated or not str(id) in response.user.games:
        return redirect("/teacher")
    if game.created == False:
        if response.method == 'POST':
            players = []
            uniquePlayers = {}
            for player in response.POST['players'].split("\n"):
                player = player.replace("\r", "")
                player = player.strip()
                if len(player) <= 0:
                    continue
                player = player.strip()  
                
                if player in uniquePlayers:
                    uniquePlayers[player] += 1
                    player = f'{player}{uniquePlayers[player]}'
                else:
                    uniquePlayers[player] = 1
                
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
    
    playerList = {}
    for player in game.players:
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
    context['week_limit_display'] = game.weekLimit if game.weekLimit < 21 else f'{game.weekLimit} (End)'

    context['finalWeek'] = False
    for player in game.players:
        playerInfo = {'username': player}
        try:
            student = Student.objects.get(username=player, code=game.code)
        except:
            continue
        try:
            gameProfile = GameProfile.objects.get(game=game, user=student.user)
            playerInfo['week'] = gameProfile.week
            if gameProfile.week > 21:
                context['finalWeek'] = True
        except:
            playerInfo['week'] = 0
        
        studentList.append(student)
        context['players'].append(playerInfo)

    context['group_cost_graph'] = groupAttributeGraph(game, studentList, 'Cost')
    context['group_yield_graph'] = groupAttributeGraph(game, studentList, 'Yield')
    if context['finalWeek']:
        context['group_leaching_graph'] = groupAttributeGraph(game, studentList, 'Leaching')
        # context['group_ae_graph'] = groupAttributeGraph(game, studentList, 'AE')
        # context['group_iwue_graph'] = groupAttributeGraph(game, studentList, 'IWUE')
        # context['group_wnipi_graph'] = groupAttributeGraph(game, studentList, 'WNIPI')
        context['group_pfp_graph'] = groupAttributeGraph(game, studentList, 'PFP')
        context['group_nue_graph'] = groupAttributeGraph(game, studentList, 'NUE')
        context['group_wue_graph'] = groupAttributeGraph(game, studentList, 'WUE')
        context['group_wp_graph'] = groupAttributeGraph(game, studentList, 'WP')

    context['urlStudent'] = f'/teacher/game/{game.id}/downloadStudents'
    context['urlTeacher'] = f'/teacher/game/{game.id}/downloadClass'

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
        message.attach_alternative(f"<p>Hello, {user.username}. This is a confirmation email for VTAPS.org. If you did not create an account recently, please disregard this message</br></br>Click <a href='https://vtaps.org/teacher/confirm/{activation_key}'> here</a> to finalize your registration with VTAPS.org</p>", "text/html")
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
        try:
            if attribute != 'Yield':
                attributeNames.append(student.username)
            gameProfile = GameProfile.objects.get(user=student.user)
            if attribute == 'Cost':
                attributeAmount.append(gameProfile.total_cost)
            elif attribute == 'PFP':
                attributeAmount.append(gameProfile.partialFactorProductivity)
            elif attribute == 'NUE':
                attributeAmount.append(gameProfile.nitrogenUseEfficiency)
            elif attribute == 'WUE':
                attributeAmount.append(gameProfile.waterUseEfficiency)
            elif attribute == 'WP':
                attributeAmount.append(gameProfile.waterProductivity)
            elif attribute == 'Leaching':
                attributeAmount.append(gameProfile.nitrogen_leaching)
            elif attribute == 'Yield':
                attributeAmount.append(gameProfile.projected_yields)    
                attributeNames.append(student.username)

        except:
            if attribute != 'Yield':
                attributeAmount.append(0)

    fig, ax = plt.subplots()


    if attribute == 'Cost':
        xlabel = 'Students'
        ylabel = 'Total Operational Costs'
        title = 'Cost Per Student'
        ax.bar(attributeNames, attributeAmount, color='skyblue')
        ax.set_ylim(bottom=750)
    # elif attribute == 'AE':
    #     xlabel = 'Students'
    #     ylabel = 'Agronimic Efficiency'
    #     title = 'Agronomic Efficiency Per Student'
    #     ax.bar(attributeNames, attributeAmount, color='skyblue')
    # elif attribute == 'IWUE':
    #     xlabel = 'Students'
    #     ylabel = 'Irrigation Water Use Efficiency'
    #     title = 'Irrigation Water Use Efficiency Per Student'
    #     ax.bar(attributeNames, attributeAmount, color='skyblue')
    # elif attribute == 'WNIPI':
    #     xlabel = 'Students'
    #     ylabel = 'Overall Efficiency Efficiency'
    #     title = 'Overall Efficiency Per Student'
    elif attribute == 'PFP':
        xlabel = 'Students'
        ylabel = 'Partial Factor Productivity'
        title = 'Partial Factor Productivity Per Student'
        ax.bar(attributeNames, attributeAmount, color='skyblue')
    elif attribute == 'NUE':
        xlabel = 'Students'
        ylabel = 'Nitrogen Use Efficiency'
        title = 'Nitrogen Use Efficiency Per Student'
        ax.bar(attributeNames, attributeAmount, color='skyblue')
    elif attribute == 'WUE':
        xlabel = 'Students'
        ylabel = 'Water Use Efficiency'
        title = 'Water Use Efficiency Per Student'
        ax.bar(attributeNames, attributeAmount, color='skyblue')
    elif attribute == 'WP':
        xlabel = 'Students'
        ylabel = 'Water Productivity'
        title = 'Water Productivity Per Student'
        ax.bar(attributeNames, attributeAmount, color='skyblue')
    elif attribute == 'Leaching':
        xlabel = 'Students'
        ylabel = 'Nitrate Leached (lbs/ac)'
        title = 'Nitrate Leached Per Student'
        ax.bar(attributeNames, attributeAmount, color='skyblue')
    elif attribute == 'Yield':
        xlabel = 'Week'
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

def downloadStudents(request, id):
    game = Game.objects.get(id=id)

    buf = io.StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(['Username', 'Week', 'Projected Yield (bu/ac)', "Monday Irrigation (in)", "Thursday Irrigation (in)", "Fertilizer (lbs)"])
    for index, player in enumerate(game.players):
        try:
            student = Student.objects.get(username=player, code=game.code)
            gameProfile = GameProfile.objects.get(user=student.user)
        except:
            continue

        for index2, pyield in enumerate(gameProfile.projected_yields):
            playerInfo = [player]
            playerInfo.append(index2+1 if index2 < 21 else 'End')
            playerInfo.append(round(pyield, 1))
            if len(gameProfile.monday_irrigation) > index2:
                playerInfo.append(gameProfile.monday_irrigation[index2])
                playerInfo.append(gameProfile.thursday_irrigation[index2])
            if index2 == 0 and len(gameProfile.weekly_fertilizer) > 0:
                playerInfo.append(gameProfile.weekly_fertilizer[0])
            elif index2 == 5 and len(gameProfile.weekly_fertilizer) > 1:
                playerInfo.append(gameProfile.weekly_fertilizer[1])
            elif index2 == 8 and len(gameProfile.weekly_fertilizer) > 2:
                playerInfo.append(gameProfile.weekly_fertilizer[2])
            elif index2 == 9 and len(gameProfile.weekly_fertilizer) > 3:
                playerInfo.append(gameProfile.weekly_fertilizer[3])
            elif index2 == 11 and len(gameProfile.weekly_fertilizer) > 4:
                playerInfo.append(gameProfile.weekly_fertilizer[4])
            elif index2 == 13 and len(gameProfile.weekly_fertilizer) > 5:
                playerInfo.append(gameProfile.weekly_fertilizer[5])
            elif index2 == 14 and len(gameProfile.weekly_fertilizer) > 6:
                playerInfo.append(gameProfile.weekly_fertilizer[6])
            elif index2 < 21:
                playerInfo.append("-")

            # if index == 0 and index2 == 0:
            #     playerInfo.append('')
            #     playerInfo.append()
            writer.writerow(playerInfo)

            if index2 == len(gameProfile.projected_yields)-1:
                writer.writerow([])

    data = buf.getvalue().encode("utf-8-sig")
        
    s3.put_object(
        Bucket="teachersummariesbucket",
        Key=f"{id}/student_summary.csv",
        Body=data,
        ContentType="text/csv",
        ContentDisposition=f'attachment; filename="student_summary_{id}.csv"',
    )

    
    key = f"{id}/student_summary.csv"

    presigned = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": "teachersummariesbucket", "Key": key},
        ExpiresIn=60
    )
    return HttpResponseRedirect(presigned)

def downloadClass(request, id):
    game = Game.objects.get(id=id)

    buf = io.StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(['Username', "Irrigation Total (in)", "Fertilizer Total (lbs)", "Final Yield (bu/ac)", "Cost Per Bushel", "Partial Factor Productivity (bu/lbs N)", "Nitrogen Utilization Efficiency (%)", "Water Utilization Efficiency (bu/in)", "Water Productivity (bu/in)", "N Leaching (lbs/ac)", "N uptake (lbs/ac)"])
    for index, player in enumerate(game.players):
        try:
            student = Student.objects.get(username=player, code=game.code)
            gameProfile = GameProfile.objects.get(user=student.user)
        except:
            continue
        
        print("gameProfile.projected_yields:", gameProfile.projected_yields)
        if len(gameProfile.projected_yields) > 0:
            irr_total = sum(gameProfile.monday_irrigation) + sum(gameProfile.thursday_irrigation)
            fert_total = sum(gameProfile.weekly_fertilizer)
            final_yield = gameProfile.projected_yields[-1]
            cost_per_bushel = gameProfile.total_cost / final_yield
            pfp = gameProfile.partialFactorProductivity
            nue = gameProfile.nitrogenUseEfficiency
            wue = gameProfile.waterUseEfficiency
            wp = gameProfile.waterProductivity
            n_leaching = gameProfile.nitrogen_leaching
            n_uptake = gameProfile.nitrogen_uptake
        
            writer.writerow([player, irr_total, fert_total, final_yield, cost_per_bushel, pfp, nue, wue, wp, n_leaching, n_uptake])

    data = buf.getvalue().encode("utf-8-sig")
        
    s3.put_object(
        Bucket="teachersummariesbucket",
        Key=f"{id}/class_summary.csv",
        Body=data,
        ContentType="text/csv",
        ContentDisposition=f'attachment; filename="class_summary_{id}.csv"',
    )

    
    key = f"{id}/class_summary.csv"

    presigned = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": "teachersummariesbucket", "Key": key},
        ExpiresIn=60
    )
    return HttpResponseRedirect(presigned)