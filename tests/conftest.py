"""Общие pytest-фикстуры."""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from app.models import Quiz, QuizSession


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def quiz_session(db):
    user = User.objects.create_user(username='fixture_user', password='pass12345')
    quiz = Quiz.objects.create(
        title='Fixture quiz',
        description='',
        created_by=user,
    )
    return QuizSession.objects.create(quiz=quiz, session_code='FXTURE')
