from django.urls import path

from . import views

urlpatterns = [
    path('', views.teacherHome, name="home"),
    path('register', views.teacherRegister, name="teacherRegister"),
    path('login', views.teacherLogin, name="teacherLogin"),
    path('logout', views.teacherLogout, name="teacherLogout"),
    path('sendEmail', views.teacherSendEmail, name="teacherSendEmail"),
]