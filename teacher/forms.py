from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from main.models import User
from .models import Teacher

class RegisterTeacherForm(UserCreationForm):
    
    class Meta:
        model = User
        widgets = {'password': forms.PasswordInput()}
        fields = ["username", "email"]

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Teacher.objects.create(user=user)
        return user

class LoginTeacherForm(AuthenticationForm):
    password = forms.PasswordInput()



class SuperuserForm(forms.Form):
    email = forms.CharField(label="email")