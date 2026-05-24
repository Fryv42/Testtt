"""Тесты репозитория для работы с игровыми сессиями QuizSession."""

import pytest
from django.contrib.auth.models import User
from app.models import Quiz, QuizSession, Participant
from app.repositories import SessionRepository


@pytest.mark.django_db
class TestSessionRepository:
    """Набор тестов для методов SessionRepository."""

    def setup_method(self):
        """Подготовка тестового окружения перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

        self.quiz = Quiz.objects.create(
            title='Test Quiz',
            description='Test Description',
            created_by=self.user,
        )

        self.code = 'ABCDEF'
        self.session = QuizSession.objects.create(
            quiz=self.quiz,
            session_code=self.code,
        )

        self.participant1 = Participant.objects.create(
            session=self.session,
            name='Alice',
        )

        self.participant2 = Participant.objects.create(
            session=self.session,
            name='Bob',
        )

    def test_get_by_id(self):
        """Проверка получения сессии по её первичному ключу (id)."""
        session = SessionRepository.get_by_id(self.session.id)
        assert session == self.session

    def test_get_by_code(self):
        """Проверка получения сессии по уникальному коду (session_code)."""
        session = SessionRepository.get_by_code(self.code)
        assert session == self.session

    def test_create(self):
        """Проверка создания новой сессии."""
        new_code = 'NEW123'
        new_session = SessionRepository.create(self.quiz, new_code)

        assert new_session.quiz == self.quiz
        assert new_session.session_code == new_code
        assert new_session.is_active

    def test_close_session(self):
        """Проверка закрытия сессии."""
        SessionRepository.close_session(self.session.id)
        self.session.refresh_from_db()

        assert not self.session.is_active

    def test_get_active_sessions(self):
        """Проверка получения списка активных сессий."""
        active_sessions = SessionRepository.get_active_sessions()
        assert self.session in active_sessions

        SessionRepository.close_session(self.session.id)

        active_sessions = SessionRepository.get_active_sessions()
        assert self.session not in active_sessions

    def test_get_participants_count(self):
        """Проверка корректного подсчёта количества участников в сессии."""
        count = SessionRepository.get_participants_count(self.session.id)
        assert count == 2

        new_session = Participant.objects.create(session=self.session, name='Charlie')
        count = SessionRepository.get_participants_count(self.session.id)
        assert count == 3