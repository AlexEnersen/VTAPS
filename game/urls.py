from django.urls import path

from . import views

urlpatterns = [
    path('', views.startGame, name="intro"),
    path('hybrid', views.pickHybrid, name="hybrid"),
    path('weekly', views.weeklySelection, name="weekly"),
    path('final', views.finalResults, name="final"),
]