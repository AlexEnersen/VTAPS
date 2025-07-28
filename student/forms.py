from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from main.models import User

class RegisterStudentForm(UserCreationForm):
    
    class Meta:
        model = User
        widgets = {'password': forms.PasswordInput()}
        fields = ["username", "email"]


class LoginStudentForm(AuthenticationForm):
    password = forms.PasswordInput()

class ConfirmStudentForm(forms.Form):
    password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput,
        validators=[validate_password],
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data