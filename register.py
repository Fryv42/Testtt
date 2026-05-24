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
from django import template
register = template.Library()
@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm
class CustomLoginView(LoginView):
    template_name = 'app/login.html'
    authentication_form = LoginForm
    def get_success_url(self):
        return '/'
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'app/register.html', {'form': form})
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, register_view
urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]
"""
{% load static %}
{% load form_extras %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <title>Вход</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"/>
</head>
<body>
<div class="container">
    <h2 class="mt-5">Вход</h2>
    {% if form.errors %}
        <div class="alert alert-danger">
            {{ form.non_field_errors }}
        </div>
    {% endif %}
    <form method="post" novalidate>
        {% csrf_token %}
        <div class="mb-3">
            <label for="id_username" class="form-label">Имя пользователя</label>
            {{ form.username|add_class:"form-control" }}
            {{ form.username.errors }}
        </div>
        <div class="mb-3">
            <label for="id_password" class="form-label">Пароль</label>
            {{ form.password|add_class:"form-control" }}
            {{ form.password.errors }}
        </div>
        <button type="submit" class="btn btn-primary">Войти</button>
        <a href="#" class="btn btn-link">Забыли пароль?</a>
    </form>
</div>
</body>
</html>
"""
"""
{% load static %}
{% load form_extras %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <title>Регистрация</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"/>
    <script>
        function validateForm() {
            let pw = document.getElementById("id_password").value;
            let pwc = document.getElementById("id_password_confirm").value;
            if (pw !== pwc) {
                alert("Пароли не совпадают!");
                return false;
            }
            return true;
        }
    </script>
</head>
<body>
<div class="container">
    <h2 class="mt-5">Регистрация</h2>
    {% if form.errors %}
        <div class="alert alert-danger">
            {{ form.non_field_errors }}
            {% for field in form %}
                {% for error in field.errors %}
                    {{ error }}<br>
                {% endfor %}
            {% endfor %}
        </div>
    {% endif %}
    <form method="post" onsubmit="return validateForm();" novalidate>
        {% csrf_token %}
        <div class="mb-3">
            <label for="id_username" class="form-label">Имя пользователя</label>
            {{ form.username|add_class:"form-control" }}
        </div>
        <div class="mb-3">
            <label for="id_email" class="form-label">Email</label>
            {{ form.email|add_class:"form-control" }}
        </div>
        <div class="mb-3">
            <label for="id_password" class="form-label">Пароль</label>
            {{ form.password|add_class:"form-control" }}
        </div>
        <div class="mb-3">
            <label for="id_password_confirm" class="form-label">Подтвердите пароль</label>
            {{ form.password_confirm|add_class:"form-control" }}
        </div>
        <button type="submit" class="btn btn-primary">Зарегистрироваться</button>
    </form>
</div>
</body>
</html>
"""
from django.test import TestCase
from django.contrib.auth.models import User
from .forms import RegisterForm, LoginForm
class RegistrationFormTest(TestCase):
    def test_valid_form(self):
        form = RegisterForm(data={
            'username': 'testuser',
            'email': 'test@test.ru',
            'password': 'pass123456',
            'password_confirm': 'pass123456',
        })
        self.assertTrue(form.is_valid())
    def test_password_mismatch(self):
        form = RegisterForm(data={
            'username': 'testuser',
            'email': 'test@test.ru',
            'password': 'pass123456',
            'password_confirm': 'wrongpass',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password_confirm', form.errors)
class LoginFormTest(TestCase):
    def setUp(self):
        User.objects.create_user(username='testuser', password='pass123456')
    def test_login_valid(self):
        form = LoginForm(data={
            'username': 'testuser',
            'password': 'pass123456',
        })
        self.assertTrue(form.is_valid())
    def test_login_invalid(self):
        form = LoginForm(data={
            'username': 'testuser',
            'password': 'wrongpass',
        })
        self.assertFalse(form.is_valid())