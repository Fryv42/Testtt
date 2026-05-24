"""
Фабрики для создания объектов (Factory Pattern).
"""
from .session_codes import generate_session_code, generate_session_code_with_prefix


class SessionCodeFactory:
    """Фабрика для генерации уникальных кодов сессий."""

    @staticmethod
    def create(length=6):
        """Создать уникальный код."""
        return generate_session_code(length)

    @staticmethod
    def create_with_prefix(prefix, length=6):
        """Создать код с префиксом."""
        return generate_session_code_with_prefix(prefix, length)
