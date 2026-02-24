from django.urls import path

from . import views

urlpatterns = [
    path("", views.runGame, name="game_singleplayer"),
    path('<int:game_id>/', views.runGame, name="game"),
    path("intro", views.intro, name="intro_singleplayer"),
    path("<int:game_id>/intro", views.intro, name="intro"),
    path('download', views.downloadResults, name="download"),
    path('download/<int:game_id>/', views.downloadResults, name="download"),
]