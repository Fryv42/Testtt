"""Тесты для HealthCheck endpoint."""
import pytest
from rest_framework.test import APIClient
from rest_framework.response import Response


@pytest.mark.django_db
class TestHealthCheck:
    """Тесты health check endpoint."""

    def setup_method(self):
        self.client = APIClient()
    
    def test_health_check(self):
        """Проверка endpoint здоровья."""
        response: Response = self.client.get('/health/')
        
        assert response.status_code == 200
        assert response.data['status'] == 'ok'