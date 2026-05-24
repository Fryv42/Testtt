from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    """Конфигурация приложения квизов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
