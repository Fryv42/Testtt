"""
Модели данных для сервиса квизов.

Соответствует минимальным функциональным требованиям ТЗ:
- Создание квиза с вопросами
- Участники и их ответы
- Статистика и результаты
"""
import random
import string

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MinValueValidator, RegexValidator
from django.db import IntegrityError, models


class Quiz(models.Model):
    """
    Викторина (квиз).

    Attributes:
        title: Название викторины
        description: Описание викторины
        created_by: Организатор (создатель)
        created_at: Дата создания
        is_active: Статус активности
    """
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        db_index=True,
        validators=[MinLengthValidator(1, message='Название не может быть пустым')],
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_quizzes',
        verbose_name="Создатель",
        db_index = True
    )
    created_at = models.DateTimeField(auto_now_add=True,
        verbose_name="Дата создания", 
        db_index = True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Викторина"
        verbose_name_plural = "Викторины"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Вопрос викторины.

    Attributes:
        quiz: Связь с викториной
        text: Текст вопроса
        order: Порядок отображения
        timer_seconds: Таймер на вопрос (опционально)
    """
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name='questions',
        verbose_name="Викторина"
    )
    text = models.TextField(
        verbose_name="Текст вопроса",
        validators=[MinLengthValidator(5, message='Минимальная длина тектса вопроса - 5 символов')]
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
        validators=[MinValueValidator(0, message='Порядковый номер не может быть отрицательным')]
    )
    timer_seconds = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Таймер (сек)"
    )

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['order']

    def __str__(self):
        return f"Question {self.order}: {self.text[:50]}"


class AnswerOption(models.Model):
    """
    Вариант ответа на вопрос.

    Attributes:
        question: Связь с вопросом
        text: Текст варианта ответа
        is_correct: Правильный ли вариант
    """
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='answers',
        verbose_name="Вопрос"
    )
    text = models.CharField(max_length=500, verbose_name="Текст ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

    def __str__(self):
        return self.text[:50]

    def clean(self):
        super().clean()
        answer_count = AnswerOption.objects.filter(question=self.question).count()
        if answer_count < 2:
            raise ValidationError(
                f"Для вопроса '{self.question.text}' должно быть минимум 2 варианта ответов."
            )


session_code_validator = RegexValidator(
    regex=r'^[A-Z0-9]{6}$',
    message="Код должен содержать 6 символов: заглавные буквы и цифры."
)


class QuizSession(models.Model):
    """
    Модель игровой сессии викторины.

    Attributes:
        quiz: Викторина, к которой относится сессия
        session_code: Уникальный код подключения участников
        started_at: Время начала сессии
        ended_at: Время завершения сессии
        is_active: Флаг активности сессии
    """

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Викторина"
    )

    session_code = models.CharField(
        max_length=6,
        unique=True,
        validators=[session_code_validator],
        verbose_name="Код сессии"
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время начала"
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время завершения"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна"
    )

    class Meta:
        verbose_name = "Сессия викторины"
        verbose_name_plural = "Сессии викторины"

    def __str__(self):
        return f"{self.quiz.title}-{self.session_code}"

    def save(self, *args, **kwargs):
        if not self.session_code:
            self.session_code = self._generate_session_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_session_code():
        characters = string.ascii_uppercase + string.digits
        for _ in range(20):
            code = ''.join(random.choices(characters, k=6))
            if not QuizSession.objects.filter(session_code=code).exists():
                return code
        raise IntegrityError('Could not generate unique session code')


class Participant(models.Model):
    """
    Участник викторины.

    Attributes:
        session: Связь с сессией
        name: Имя участника
        joined_at: Время подключения
        total_score: Общий балл
    """

    session = models.ForeignKey(
        QuizSession,
        on_delete=models.CASCADE,
        related_name='participants',
        db_index=True,
        verbose_name="Сессия"
    )

    name = models.CharField(
        max_length=100,
        verbose_name='Имя',
        validators=[MinLengthValidator(1, message='Имя участника не может быть пустым')],
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Подключился"
    )

    total_score = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="Баллы"
    )

    class Meta:
        verbose_name = "Участник"
        verbose_name_plural = "Участники"
        ordering = ["-total_score", "joined_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["session", "name"],
                name="unique_participant_name_in_session"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.session.session_code})"

class ParticipantAnswer(models.Model):
    """
    Ответ участника на вопрос.
    """
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='answers',
        verbose_name="Участник",
        db_index=True  # ИСПРАВЛЕНО: Добавлен индекс
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, 
        verbose_name="Вопрос",
        db_index=True  # ИСПРАВЛЕНО: Добавлен индекс
    )
    answer = models.ForeignKey(
        AnswerOption, on_delete=models.CASCADE, 
        verbose_name="Ответ",
        db_index=True  # ИСПРАВЛЕНО: Добавлен индекс
    )
    is_correct = models.BooleanField(default=False, verbose_name="Правильно")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Время ответа")
    response_time_seconds = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Время ответа (сек)",
    )

    class Meta:
        verbose_name = "Ответ участника"
        verbose_name_plural = "Ответы участников"
        unique_together = ['participant', 'question']

    def __str__(self):
        return f"{self.participant.name} - {self.question.text[:30]}"

    def clean(self):
        if self.answer.question_id != self.question_id:
            raise ValidationError("Выбранный вариант ответа не относится к этому вопросу.")
