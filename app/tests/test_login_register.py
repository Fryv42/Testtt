from django.test import TestCase
from django.contrib.auth.models import User
from forms import RegisterForm, LoginForm

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