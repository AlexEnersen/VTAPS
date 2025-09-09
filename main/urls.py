from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('reset', views.reset, name="reset"),
    path('download/<int:team_id>', views.downloadResults, name="download")
]