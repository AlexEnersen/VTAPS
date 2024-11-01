from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import LoginTeacherForm, RegisterTeacherForm
from django.core import mail
from django.core.mail import EmailMultiAlternatives

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

        return redirect("/teacher")
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

def sendConfirmationEmail(user):

    connection = mail.get_connection()
    connection.open()

    message = EmailMultiAlternatives("Hello from Django", "This is a test", "enersen1995@gmail.com", ["stephen.cooper@unl.edu"], connection=connection)
    message.attach_alternative("<p>Hi, Dr. Cooper! I'm sending this from Django. This is a prototype of a confirmation email for teachers.</br></br> <a href=https://taps.unl.edu/>Click Here</a> to finalize your registration with VTAPS</br>(I can't link to localhost, so I'm linking to the VTAPS website for now)</p>", "text/html")
    message.send()

    connection.close()