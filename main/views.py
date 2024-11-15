from django.shortcuts import render
from django.contrib.sessions.models import Session

def home(response):
    # response.session.clear()
    print('HOME IS HERE!!!!')
    Session.objects.all().delete()
    user_id = response.session.get("user_id", None)
    if not user_id == None:
        return render(response, 'main/home.html', {"user_id": user_id})
    return render(response, 'main/home.html', {})