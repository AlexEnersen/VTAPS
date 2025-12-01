from django import forms
from django.forms import ModelForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from main.models import User
from .models import Teacher, WeekEntries

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
    username = forms.CharField(max_length=64, label="Username")
    password = forms.PasswordInput()
    
    error_messages = {
        "invalid_login": "Invalid credentials. Check username and password.",
        "inactive": "This account is inactive.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()     # gets field-cleaned data
        username = cleaned.get("local_username")
        password = cleaned.get("password")

        # custom cross-field logic:
        if username and password:
            user = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if user is None:
                raise forms.ValidationError(self.error_messages["invalid_login"])
            if not user.is_active:
                raise forms.ValidationError(self.error_messages["inactive"])
            self.user_cache = user

        return cleaned

class SuperuserForm(forms.Form):
    email = forms.CharField(label="email")

class WeekForm(ModelForm):
    class Meta:
        model = WeekEntries
        fields = '__all__'