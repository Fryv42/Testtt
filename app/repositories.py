"""Репозитории для работы с данными (Repository Pattern)."""
from django.contrib.auth.models import User
from .models import Participant, Quiz, QuizSession


class QuizRepository:
    """Репозиторий для работы с викторинами."""

    @staticmethod
    def get_by_id(quiz_id):
        """Получить викторину по ID."""
        return Quiz.objects.get(id=quiz_id)

    @staticmethod
    def get_active_by_user(user):
        """Получить активные викторины пользователя."""
        return Quiz.objects.filter(created_by=user, is_active=True)

    @staticmethod
    def create(title, description, user):
        """Создать викторину."""
        return Quiz.objects.create(
            title=title,
            description=description,
            created_by=user
        )


class SessionRepository:
    """Репозиторий для работы с сессиями викторин."""

    @staticmethod
    def get_by_id(session_id: int) -> QuizSession:
        """
        Получить сессию по её ID.

        Args:
            session_id: ID сессии.

        Returns:
            QuizSession: объект сессии.
        """
        return QuizSession.objects.get(id=session_id)

    @staticmethod
    def get_by_code(code: str) -> QuizSession:
        """Получить сессию по коду."""
        return QuizSession.objects.get(session_code=code)

    @staticmethod
    def get_active_sessions():
        """
        Получить все активные сессии.

        Returns:
            QuerySet[QuizSession]: список активных сессий.
        """
        return QuizSession.objects.filter(is_active=True)

    @staticmethod
    def create(quiz: Quiz, session_code: str) -> QuizSession:
        """Создать сессию."""
        return QuizSession.objects.create(quiz=quiz, session_code=session_code)

    @staticmethod
    def close_session(session_id: int) -> None:
        """
        Закрыть сессию (установить is_active = False).

        Args:
            session_id: ID сессии.
        """
        QuizSession.objects.filter(id=session_id).update(is_active=False)

    @staticmethod
    def get_participants_count(session_id: int) -> int:
        """
        Получить количество участников в сессии.

        Args:
            session_id: ID сессии.

        Returns:
            int: количество участников.
        """
        return Participant.objects.filter(session_id=session_id).count()