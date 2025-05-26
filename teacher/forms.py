from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Teacher

class RegisterTeacherForm(UserCreationForm):
    
    class Meta:
        model = Teacher
        widgets = {'password': forms.PasswordInput()}
        fields = ["username", "email"]


class LoginTeacherForm(AuthenticationForm):
    password = forms.PasswordInput()



class SuperuserForm(forms.Form):
    email = forms.CharField(label="email")