from django import forms
from django.db import models
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from main.models import User

class LoginStudentForm(forms.Form):
    class_code = forms.CharField(max_length=16, label="Class Code")
    local_username = forms.CharField(max_length=64, label="Username")
    password = forms.CharField(max_length=256, widget=forms.PasswordInput)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['class_room', 'local_username'],
                                    name='uniq_local_username_per_class')
        ]

    error_messages = {
        "invalid_login": "Invalid credentials. Check class code, username, and password.",
        "inactive": "This account is inactive.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()     # gets field-cleaned data
        class_code = cleaned.get("class_code")
        username = cleaned.get("local_username")
        password = cleaned.get("password")

        # custom cross-field logic:
        if class_code and username and password:
            user = authenticate(
                self.request,
                code=class_code,
                username=username,
                password=password,
            )
            if user is None:
                raise forms.ValidationError(self.error_messages["invalid_login"])
            if not user.is_active:
                raise forms.ValidationError(self.error_messages["inactive"])
            self.user_cache = user

        return cleaned
    
    def get_user(self):
        return self.user_cache