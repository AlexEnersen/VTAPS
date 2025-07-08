from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from main.models import User

class RegisterStudentForm(UserCreationForm):
    
    class Meta:
        model = User
        widgets = {'password': forms.PasswordInput()}
        fields = ["username", "email"]


class LoginStudentForm(AuthenticationForm):
    password = forms.PasswordInput()

