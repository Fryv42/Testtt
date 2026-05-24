"""Тесты статистики викторины."""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from app.models import (
    AnswerOption,
    Participant,
    ParticipantAnswer,
    Question,
    Quiz,
    QuizSession,
)


@pytest.mark.django_db
class TestQuizStatistics:
    """Проверка endpoint статистики по викторине."""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='stats_user', password='pass1234')
        self.quiz = Quiz.objects.create(
            title='Test Quiz',
            created_by=self.user,
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text='Test Question',
            order=1,
        )
        correct = AnswerOption.objects.create(
            question=self.question,
            text='Yes',
            is_correct=True,
        )
        wrong = AnswerOption.objects.create(
            question=self.question,
            text='No',
            is_correct=False,
        )

        session = QuizSession.objects.create(quiz=self.quiz, session_code='ST0001')
        participants = [
            Participant.objects.create(session=session, name=f'Player {index}')
            for index in range(3)
        ]

        ParticipantAnswer.objects.create(
            participant=participants[0],
            question=self.question,
            answer=correct,
            is_correct=True,
            response_time_seconds=2.0,
        )
        ParticipantAnswer.objects.create(
            participant=participants[1],
            question=self.question,
            answer=correct,
            is_correct=True,
            response_time_seconds=4.0,
        )
        ParticipantAnswer.objects.create(
            participant=participants[2],
            question=self.question,
            answer=wrong,
            is_correct=False,
            response_time_seconds=6.0,
        )

    def test_statistics(self):
        url = f'/api/v1/quizzes/{self.quiz.id}/statistics/'
        response = self.client.get(url)

        assert response.status_code == 200
        data = response.data['results'][0]
        assert data['participants_count'] == 3
        assert data['correct_answer_rate'] == pytest.approx(66.67, abs=0.1)
        assert data['average_response_time'] == pytest.approx(4.0, abs=0.1)
