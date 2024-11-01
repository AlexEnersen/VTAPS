from django.shortcuts import render

def home(response):
    # response.session.clear()
    user_id = response.session.get("user_id", None)
    if not user_id == None:
        return render(response, 'main/home.html', {"user_id": user_id})
    return render(response, 'main/home.html', {})