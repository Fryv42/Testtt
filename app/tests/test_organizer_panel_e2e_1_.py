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
def organizer(db):
    return User.objects.create_user(username="organizer", password="StrongPass123!")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="other", password="StrongPass123!")


@pytest.fixture
def client(organizer):
    c = APIClient()
    c.force_authenticate(user=organizer)
    return c


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def quiz(organizer):
    q = Quiz.objects.create(title="History Quiz", created_by=organizer, is_active=True)
    q1 = Question.objects.create(quiz=q, text="Who was the first US president?", order=1)
    q2 = Question.objects.create(quiz=q, text="When did WW2 end?", order=2)

    AnswerOption.objects.create(question=q1, text="Washington", is_correct=True)
    AnswerOption.objects.create(question=q1, text="Lincoln", is_correct=False)
    AnswerOption.objects.create(question=q2, text="1945", is_correct=True)
    AnswerOption.objects.create(question=q2, text="1939", is_correct=False)

    return q


@pytest.fixture
def session(quiz):
    s = QuizSession.objects.create(quiz=quiz, session_code="ORG001", is_active=False)

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
class TestOrganizerAccess:
    def test_organizer_can_access_quiz_list(self, client):
        resp = client.get("/api/v1/quizzes/")
        assert resp.status_code == 200

    def test_anonymous_cannot_create_quiz(self, anon_client):
        resp = anon_client.post("/api/v1/quizzes/", {
            "title": "Hack",
            "questions": [{"text": "Q?", "order": 1}]
        }, format="json")
        assert resp.status_code == 403

    def test_nonexistent_quiz_returns_404(self, client):
        resp = client.get("/api/v1/quizzes/99999/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestSessionFiltering:
    def test_filter_active_sessions(self, client, quiz):
        QuizSession.objects.create(quiz=quiz, session_code="FIL001", is_active=True)
        QuizSession.objects.create(quiz=quiz, session_code="FIL002", is_active=False)

        resp = client.get("/api/v1/sessions/?is_active=true")
        assert resp.status_code == 200
        data = resp.data.get("results") or resp.data
        assert all(s["is_active"] for s in data)

    def test_filter_inactive_sessions(self, client, quiz):
        QuizSession.objects.create(quiz=quiz, session_code="FIL003", is_active=True)
        QuizSession.objects.create(quiz=quiz, session_code="FIL004", is_active=False)

        resp = client.get("/api/v1/sessions/?is_active=false")
        assert resp.status_code == 200
        data = resp.data.get("results") or resp.data
        assert all(not s["is_active"] for s in data)

    def test_filter_by_quiz(self, client, quiz, organizer):
        other = Quiz.objects.create(title="Other", created_by=organizer, is_active=True)
        QuizSession.objects.create(quiz=quiz, session_code="FIL005", is_active=True)
        QuizSession.objects.create(quiz=other, session_code="FIL006", is_active=True)

        resp = client.get(f"/api/v1/sessions/?quiz={quiz.id}")
        assert resp.status_code == 200
        data = resp.data.get("results") or resp.data
        assert all(s["quiz"] == quiz.id for s in data)


@pytest.mark.django_db
class TestParticipantOrdering:
    def test_participants_ordered_by_score_desc_in_db(self, session):
        participants = list(session.participants.all())
        scores = [p.total_score for p in participants]
        assert scores == sorted(scores, reverse=True)

    def test_participant_count_in_session(self, session):
        assert session.participants.count() == 3


@pytest.mark.django_db
class TestQuestionStatistics:
    def test_correct_answer_count_per_question(self, session):
        for question in session.quiz.questions.all():
            correct = ParticipantAnswer.objects.filter(
                question=question, is_correct=True
            ).count()
            total = ParticipantAnswer.objects.filter(question=question).count()

            assert total == 3
            assert correct == 1

    def test_correct_answer_percentage(self, session):
        question = session.quiz.questions.first()
        correct = ParticipantAnswer.objects.filter(
            question=question, is_correct=True
        ).count()
        total = ParticipantAnswer.objects.filter(question=question).count()

        assert round(correct / total * 100, 1) == 33.3

    def test_all_questions_have_answers(self, session):
        for question in session.quiz.questions.all():
            assert ParticipantAnswer.objects.filter(question=question).exists()


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
