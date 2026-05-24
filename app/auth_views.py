"""Представления входа и регистрации."""
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm


class CustomLoginView(LoginView):
    """Страница входа."""

    template_name = 'app/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        return '/'


def register_view(request):
    """Регистрация пользователя и автоматический вход."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    return render(request, 'app/register.html', {'form': form})
