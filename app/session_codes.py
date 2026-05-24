"""Генерация уникальных кодов игровых сессий."""
import random
import re
import string

from django.apps import apps

ALPHABET = string.ascii_uppercase + string.digits
VALID_PATTERN = re.compile(r'^[A-Z0-9]+$')


def _quiz_session_model():
    return apps.get_model('app', 'QuizSession')


def generate_session_code(length=6):
    """Создать уникальный код сессии заданной длины."""
    quiz_session = _quiz_session_model()
    while True:
        code = ''.join(random.choices(ALPHABET, k=length))
        if not quiz_session.objects.filter(session_code=code).exists():
            return code


def generate_session_code_with_prefix(prefix, length=6):
    """Создать уникальный код сессии с префиксом."""
    prefix = prefix.upper()
    if not VALID_PATTERN.match(prefix):
        raise ValueError('Session code prefix must contain only A-Z and 0-9')

    quiz_session = _quiz_session_model()
    while True:
        code = prefix + ''.join(random.choices(ALPHABET, k=length))
        if not quiz_session.objects.filter(session_code=code).exists():
            return code
