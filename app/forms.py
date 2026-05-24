"""Формы аутентификации и регистрации."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True, 'required': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'required': True}))

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Подтвердите пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_password_confirm(self):
        pw = self.cleaned_data.get("password")
        pwc = self.cleaned_data.get("password_confirm")
        if pw and pwc and pw != pwc:
            raise forms.ValidationError("Пароли не совпадают!")
        return pwc

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
