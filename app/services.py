"""Сервисы экспорта и статистики викторин."""
import csv
import io

from django.db.models import Avg, Count, Q

from .models import Question


def generate_session_csv(session):
    """
    Формирует CSV с результатами участников сессии.

    Args:
        session: Экземпляр ``QuizSession``.

    Returns:
        str: Содержимое CSV-файла в кодировке UTF-8 с BOM.
    """
    output = io.StringIO()
    output.write('\ufeff')

    writer = csv.writer(output)
    writer.writerow([
        'Имя',
        'Общий балл',
        'Правильные ответы',
        'Время последнего ответа',
    ])

    participants = session.participants.annotate(
        correct_count=Count('answers', filter=Q(answers__is_correct=True)),
    ).order_by('-total_score')

    for participant in participants:
        last_response = participant.answers.order_by('-answered_at').first()
        time_str = (
            last_response.answered_at.strftime('%Y-%m-%d %H:%M')
            if last_response
            else '—'
        )
        writer.writerow([
            participant.name,
            participant.total_score,
            participant.correct_count,
            time_str,
        ])

    return output.getvalue()


def get_quiz_statistics(quiz_id):
    """
    Возвращает статистику ответов по каждому вопросу викторины.

    Args:
        quiz_id: Идентификатор викторины.

    Returns:
        list[dict]: Список словарей со статистикой по вопросам.
    """
    queryset = Question.objects.filter(quiz_id=quiz_id).annotate(
        total_answers=Count('participantanswer'),
        correct_answers=Count(
            'participantanswer',
            filter=Q(participantanswer__is_correct=True),
        ),
        participants=Count('participantanswer__participant', distinct=True),
        avg_time=Avg('participantanswer__response_time_seconds'),
    )

    stats = []

    for question in queryset:
        total = question.total_answers or 0
        correct = question.correct_answers or 0
        correct_rate = (correct / total * 100) if total > 0 else 0

        stats.append({
            'question_id': question.id,
            'question_text': question.text,
            'correct_answer_rate': round(correct_rate, 2),
            'average_response_time': round(question.avg_time or 0, 2),
            'participants_count': question.participants,
        })

    return stats
