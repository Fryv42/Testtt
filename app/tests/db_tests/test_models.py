"""Тесты моделей приложения."""

import time
import pytest
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from app.models import (
    Quiz, 
    Question, 
    AnswerOption, 
    QuizSession, 
    Participant, 
    ParticipantAnswer,
)


@pytest.mark.django_db
class TestQuizModel:
    """Тесты модели Quiz."""

    def setup_method(self):
        """Создание тестового пользователя перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
        )

    def test_quiz_creation(self):
        """Проверка создания квиза с корректными данными."""
        quiz = Quiz.objects.create(
            title="Тестовый квиз",
            description="Описание",
            created_by=self.user,
        )

        assert quiz.title == "Тестовый квиз"
        assert quiz.is_active is True
        assert quiz.created_by == self.user

    def test_quiz_creation_with_not_enough_data(self):
        """Проверка, что пустой title не проходит валидацию."""
        quiz = Quiz(
            title='',
            description='Описание',
            created_by=self.user,
        )
        with pytest.raises(ValidationError):
            quiz.full_clean()
    
    def test_quiz_str(self):
        """Проверка строкового представления квиза."""
        quiz = Quiz.objects.create(
            title="Тестовый квиз",
            created_by=self.user,
        )

        assert str(quiz) == "Тестовый квиз"


@pytest.mark.django_db
class TestQuestionModel:
    """Тесты модели Question."""

    def setup_method(self):
        """Создание пользователя и квиза перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
        )

        self.quiz = Quiz.objects.create(
            title="Тестовый квиз",
            created_by=self.user,
        )

    def test_question_creation(self):
        """Проверка создания вопроса с корректными данными."""
        question = Question.objects.create(
            quiz=self.quiz,
            text="Тестовый вопрос?",
            order=1,
        )

        assert question.quiz == self.quiz
        assert question.text == "Тестовый вопрос?"
        assert question.order == 1
        assert question.timer_seconds is None

    def test_question_creation_not_enough_length(self):
        """Проверка, что вопрос с текстом короче 5 символов не должен проходить валидацию модели."""
        question = Question.objects.create(
            quiz=self.quiz,
            text="???",
            order=1,
        )
        
        with pytest.raises(ValidationError):
            question.full_clean()

    def test_question_creation_order_negative(self):
        """Проверка, что отрицательное значение order не может быть."""
        with pytest.raises(IntegrityError):
            question = Question.objects.create(
                quiz=self.quiz,
                text="???",
                order=-1,
            )

            with pytest.raises(ValidationError):
                question.full_clean()

    def test_delete_quiz_cascade(self):
        """Проверка каскадного удаления."""
        question = Question.objects.create(
            quiz=self.quiz,
            text="Тестовый вопрос?",
            order=1,
        )

        self.quiz.delete()

        assert not Question.objects.filter(text="Тестовый вопрос?").exists()

    def test_questions_ordering_by_order(self):
        """Проверка сортировки вопросов по полю order."""
        question1 = Question.objects.create(
            quiz=self.quiz,
            text="Первый вопрос",
            order=10,
        )
        question2 = Question.objects.create(
            quiz=self.quiz,
            text="Второй вопрос",
            order=5,
        )
        question3 = Question.objects.create(
            quiz=self.quiz,
            text="Третий вопрос",
            order=1,
        )
        
        questions: list[Question] = list(self.quiz.questions.all())
        
        assert questions[0].order == 1
        assert questions[1].order == 5
        assert questions[2].order == 10


@pytest.mark.django_db
class TestAnswerOptionModel:
    """Тесты модели AnswerOption."""

    def setup_method(self):
        """Создание пользователя, квиза и вопроса перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
        )

        self.quiz = Quiz.objects.create(
            title="Тестовый квиз",
            created_by=self.user,
        )

        self.question = Question.objects.create(
            quiz=self.quiz,
            text="Тестовый вопрос?",
            order=1,
        )

    def test_answer_creation(self):
        """Проверка создания варианта ответа."""
        answer = AnswerOption.objects.create(
            question=self.question,
            text="Правильный ответ",
            is_correct=True,
        )

        assert answer.question == self.question
        assert answer.text == "Правильный ответ"
        assert answer.is_correct is True


@pytest.mark.django_db
class TestQuizSessionModel:
    """Тесты модели QuizSession."""

    def setup_method(self):
        """Создание пользователя и квиза перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
        )

        self.quiz = Quiz.objects.create(
            title="Тестовый квиз",
            created_by=self.user,
        )

    def test_session_creation(self):
        """Проверка создания игровой сессии с явным кодом."""
        session = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="ABC123",
        )

        assert session.quiz == self.quiz
        assert session.session_code == "ABC123"
        assert session.is_active is True
        assert session.started_at is not None
        assert session.ended_at is None

    def test_session_auto_generate_code(self):
        """Проверка, что код сессии генерируется автоматически, если не указан."""
        session = QuizSession.objects.create(
            quiz=self.quiz,
        )

        assert session.session_code is not None

    def test_session_code_unique(self):
        """Проверка, что код сессии уникален."""
        QuizSession.objects.create(
            quiz=self.quiz,
            session_code="UNIQ12",
        )

        with pytest.raises(IntegrityError):
            QuizSession.objects.create(
                quiz=self.quiz,
                session_code="UNIQ12",
            )

    def test_session_str(self):
        """Проверка строкового представления сессии."""
        session = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="STR123",
        )

        assert str(session) == f"{self.quiz.title}-STR123"

    def test_quiz_cascade_delete(self):
        """Проверка, что при удалении квиза удаляются и его сессии."""
        session = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="CASCADE",
        )

        self.quiz.delete()

        assert not QuizSession.objects.filter(id=session.id).exists()

    def test_ordering_by_started_at(self):
        """Проверка сортировки сессий по дате начала."""
        session1 = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="ORDER1",
        )
        
        time.sleep(0.01)
        session2 = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="ORDER2",
        )

        sessions_desc = QuizSession.objects.order_by('-started_at')

        assert sessions_desc[0] == session2
        assert sessions_desc[1] == session1


@pytest.mark.django_db
class TestParticipantModel:
    """Тесты модели Participant."""

    def setup_method(self):
        """Создание пользователя, квиза и сессии перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
        )

        self.quiz = Quiz.objects.create(
            title="Тестовый квиз",
            created_by=self.user,
        )

        self.session1 = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="ABC123",
        )
        self.session2 = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="DEF456",
        )

    def test_participant_creation(self):
        """Проверка создания участника с корректными данными."""
        participant = Participant.objects.create(
            session=self.session1,
            name="Иван",
        )

        assert participant.session == self.session1
        assert participant.name == "Иван"
        assert participant.total_score == 0
        assert participant.joined_at is not None

    def test_participant_total_score_default(self):
        """Проверка, что total_score по умолчанию равен 0."""
        participant = Participant.objects.create(
            session=self.session1,
            name="Петр",
        )

        assert participant.total_score == 0

    def test_participant_str(self):
        """Проверка строкового представления участника."""
        participant = Participant.objects.create(
            session=self.session1,
            name="Алексей",
        )

        assert str(participant) == f"Алексей ({self.session1.session_code})"

    def test_unique_name_per_session(self):
        """Проверка уникальности имени участника в рамках одной сессии."""
        Participant.objects.create(
            session=self.session1,
            name="Дубликат",
        )

        with pytest.raises(IntegrityError):
            Participant.objects.create(
                session=self.session1,
                name="Дубликат",
            )

    def test_same_name_different_sessions_allowed(self):
        """Проверка, что одинаковые имена допустимы в разных сессиях."""
        participant1 = Participant.objects.create(
            session=self.session1,
            name="Общее имя",
        )
        participant2 = Participant.objects.create(
            session=self.session2,
            name="Общее имя",
        )

        assert participant1.name == participant2.name
        assert participant1.session != participant2.session

    def test_cascade_delete_session(self):
        """Проверка, что при удалении сессии удаляются и её участники."""
        participant = Participant.objects.create(
            session=self.session1,
            name="Каскад",
        )

        self.session1.delete()

        assert not Participant.objects.filter(id=participant.id).exists()

    def test_ordering_by_score_then_joined_at(self):
        """Проверка сортировки участников."""
        participant_a = Participant.objects.create(
            session=self.session1,
            name="A (50 очков, раньше)",
            total_score=50,
        )

        time.sleep(0.01)

        participant_b = Participant.objects.create(
            session=self.session1,
            name="B (50 очков, позже)",
            total_score=50,
        )

        participant_c = Participant.objects.create(
            session=self.session1,
            name="C (100 очков)",
            total_score=100,
        )

        participant_d = Participant.objects.create(
            session=self.session1,
            name="D (0 очков)",
            total_score=0,
        )

        participants = list(Participant.objects.filter(session=self.session1))

        assert participants[0].name == "C (100 очков)"
        assert participants[1].name == "A (50 очков, раньше)"
        assert participants[2].name == "B (50 очков, позже)"
        assert participants[3].name == "D (0 очков)"

    def test_negative_total_score_not_allowed(self):
        """Проверка, что total_score не может быть отрицательным."""
        with pytest.raises(IntegrityError):
            participant = Participant(
                session=self.session1,
                name="Отрицатель",
                total_score=-5,
            )

            participant.save()

    def test_participant_name_max_length(self):
        """Проверка, что имя не может превышать max_length."""
        participant = Participant(
            session=self.session1,
            name="A" * 101,
        )

        with pytest.raises(ValidationError):
            participant.full_clean()

    def test_participant_name_required(self):
        """Проверка, что поле name обязательно для заполнения."""
        participant = Participant(session=self.session1, name='')
        with pytest.raises(ValidationError):
            participant.full_clean()


@pytest.mark.django_db
class TestParticipantAnswerModel:
    """Тесты модели ParticipantAnswer."""

    def setup_method(self):
        """Создание всей цепочки данных: пользователь, квиз, вопрос, вариант ответа, сессия, участник."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
        )

        self.quiz = Quiz.objects.create(
            title="Тестовый квиз",
            created_by=self.user,
        )

        self.question = Question.objects.create(
            quiz=self.quiz,
            text="Тестовый вопрос?",
            order=1,
        )

        self.answer = AnswerOption.objects.create(
            question=self.question,
            text="Правильный ответ",
            is_correct=True,
        )

        self.session = QuizSession.objects.create(
            quiz=self.quiz,
            session_code="ABC123",
        )

        self.participant = Participant.objects.create(
            session=self.session,
            name="Иван",
        )

    def test_answer_creation(self):
        """Проверка создания ответа участника."""
        participant_answer = ParticipantAnswer.objects.create(
            participant=self.participant,
            question=self.question,
            answer=self.answer,
            is_correct=True,
        )

        assert participant_answer.participant == self.participant
        assert participant_answer.question == self.question
        assert participant_answer.answer == self.answer
        assert participant_answer.is_correct is True