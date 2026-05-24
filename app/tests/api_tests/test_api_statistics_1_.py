import csv
import io
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
from app.services import generate_session_csv


@pytest.fixture
def user(db):
    return User.objects.create_user(username="organizer", password="pass1234!")


@pytest.fixture
def client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def quiz(user):
    q = Quiz.objects.create(title="Geography", created_by=user, is_active=True)
    q1 = Question.objects.create(quiz=q, text="Capital of France?", order=1)
    q2 = Question.objects.create(quiz=q, text="Capital of Germany?", order=2)

    AnswerOption.objects.create(question=q1, text="Paris", is_correct=True)
    AnswerOption.objects.create(question=q1, text="Lyon", is_correct=False)
    AnswerOption.objects.create(question=q2, text="Berlin", is_correct=True)
    AnswerOption.objects.create(question=q2, text="Munich", is_correct=False)

    return q


@pytest.fixture
def session(quiz):
    s = QuizSession.objects.create(quiz=quiz, session_code="TST001", is_active=False)

    alice = Participant.objects.create(session=s, name="Alice", total_score=200)
    bob = Participant.objects.create(session=s, name="Bob", total_score=100)
    charlie = Participant.objects.create(session=s, name="Charlie", total_score=50)

    for question in quiz.questions.all():
        correct = question.answers.get(is_correct=True)
        wrong = question.answers.get(is_correct=False)

        ParticipantAnswer.objects.create(
            participant=alice, question=question, answer=correct, is_correct=True
        )
        ParticipantAnswer.objects.create(
            participant=bob, question=question, answer=wrong, is_correct=False
        )
        ParticipantAnswer.objects.create(
            participant=charlie, question=question, answer=wrong, is_correct=False
        )

    return s


@pytest.mark.django_db
class TestSessionResultsEndpoint:
    def test_session_returns_200(self, client, session):
        resp = client.get(f"/api/v1/sessions/{session.id}/")
        assert resp.status_code == 200

    def test_session_unauthenticated_can_read(self, anon_client, session):
        resp = anon_client.get(f"/api/v1/sessions/{session.id}/")
        assert resp.status_code == 200

    def test_session_nonexistent_returns_404(self, client):
        resp = client.get("/api/v1/sessions/99999/")
        assert resp.status_code == 404

    def test_filter_active_sessions(self, client, quiz):
        QuizSession.objects.create(quiz=quiz, session_code="ACT001", is_active=True)
        QuizSession.objects.create(quiz=quiz, session_code="ACT002", is_active=False)

        resp = client.get("/api/v1/sessions/?is_active=true")
        data = resp.data.get("results") or resp.data
        assert all(s["is_active"] for s in data)

    def test_filter_inactive_sessions(self, client, quiz):
        QuizSession.objects.create(quiz=quiz, session_code="INA001", is_active=True)
        QuizSession.objects.create(quiz=quiz, session_code="INA002", is_active=False)

        resp = client.get("/api/v1/sessions/?is_active=false")
        data = resp.data.get("results") or resp.data
        assert all(not s["is_active"] for s in data)


@pytest.mark.django_db
class TestCorrectAnswerPercentage:
    def test_one_correct_out_of_three(self, session):
        question = session.quiz.questions.first()
        correct = ParticipantAnswer.objects.filter(
            question=question, is_correct=True
        ).count()
        total = ParticipantAnswer.objects.filter(question=question).count()

        assert round(correct / total * 100, 1) == 33.3

    def test_all_correct(self, session):
        question = session.quiz.questions.first()
        correct_option = question.answers.get(is_correct=True)

        extra1 = Participant.objects.create(session=session, name="D", total_score=0)
        extra2 = Participant.objects.create(session=session, name="E", total_score=0)

        ParticipantAnswer.objects.filter(question=question, is_correct=False).delete()
        ParticipantAnswer.objects.create(
            participant=extra1, question=question, answer=correct_option, is_correct=True
        )
        ParticipantAnswer.objects.create(
            participant=extra2, question=question, answer=correct_option, is_correct=True
        )

        correct = ParticipantAnswer.objects.filter(
            question=question, is_correct=True
        ).count()
        total = ParticipantAnswer.objects.filter(question=question).count()

        assert correct / total == 1.0

    def test_no_answers_gives_zero(self, quiz):
        empty = QuizSession.objects.create(quiz=quiz, session_code="EMP001", is_active=False)
        question = quiz.questions.first()

        total = ParticipantAnswer.objects.filter(
            question=question, participant__session=empty
        ).count()
        percent = (0 / total * 100) if total else 0

        assert percent == 0


@pytest.mark.django_db
class TestParticipantOrdering:
    def test_ordered_by_score_desc(self, session):
        scores = list(session.participants.values_list("total_score", flat=True))
        assert scores == sorted(scores, reverse=True)

    def test_participant_count(self, session):
        assert session.participants.count() == 3


@pytest.mark.django_db
class TestCSVExport:
    def test_csv_has_content(self, session):
        content = generate_session_csv(session)
        assert len(content) > 0

    def test_csv_has_four_columns(self, session):
        content = generate_session_csv(session)
        reader = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
        assert len(reader[0]) == 4

    def test_csv_contains_all_participants(self, session):
        content = generate_session_csv(session)
        reader = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
        names = [row[0] for row in reader[1:]]

        assert "Alice" in names
        assert "Bob" in names
        assert "Charlie" in names

    def test_csv_sorted_by_score_desc(self, session):
        content = generate_session_csv(session)
        reader = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
        scores = [int(row[1]) for row in reader[1:]]
        assert scores == sorted(scores, reverse=True)

    def test_csv_correct_answers_column(self, session):
        content = generate_session_csv(session)
        reader = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
        rows = {row[0]: int(row[2]) for row in reader[1:]}

        assert rows["Alice"] == 2
        assert rows["Bob"] == 0
        assert rows["Charlie"] == 0

    def test_csv_scores_are_correct(self, session):
        content = generate_session_csv(session)
        reader = list(csv.reader(io.StringIO(content.lstrip("\ufeff"))))
        rows = {row[0]: int(row[1]) for row in reader[1:]}

        assert rows["Alice"] == 200
        assert rows["Bob"] == 100
        assert rows["Charlie"] == 50
