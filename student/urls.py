from django.urls import path

from . import views

urlpatterns = [
    path('', views.studentHome, name="home"),
    path('register', views.studentRegister, name="studentRegister"),
    path('login', views.studentLogin, name="studentLogin"),
    path('logout', views.studentLogout, name="studentLogout"),
    path('confirm/<str:activation_key>/', views.studentConfirm, name='studentConfirm')
    ]