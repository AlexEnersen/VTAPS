from django.urls import path

from . import views
from game import views as gameviews 

urlpatterns = [
    path('', views.studentHome, name="home"),
    path('login', views.studentLogin, name="studentLogin"),
    path('logout', views.studentLogout, name="studentLogout"),
    ]