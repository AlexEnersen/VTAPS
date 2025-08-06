from django.urls import path

from . import views

urlpatterns = [
    path("", views.runGame, name="game_singleplayer"),
    path('<int:game_id>/', views.runGame, name="game"),
    # path('hybrid', views.pickHybrid, name="hybrid"),
    # path('weekly', views.weeklySelection, name="weekly"),
    # path('final', views.finalResults, name="final"),
]