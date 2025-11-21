from django.urls import path

from . import views

urlpatterns = [
    path('', views.teacherHome, name="home"),
    path('register', views.teacherRegister, name="teacherRegister"),
    path('login', views.teacherLogin, name="teacherLogin"),
    path('logout', views.teacherLogout, name="teacherLogout"),
    path('newGame', views.newGame, name="newGame"),
    path('game/<int:id>', views.game, name="game"),
    path('sendEmail', views.teacherSendEmail, name="teacherSendEmail"),
    path('confirm/<str:activation_key>/', views.teacherConfirm, name='teacherConfirm'),
    path('createGame/<int:id>/', views.createGame, name="createGame"),
    path('game/<int:id>/download', views.download, name="download")
]