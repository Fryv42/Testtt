"""Тесты для Version endpoint."""
import pytest
from rest_framework.test import APIClient
from rest_framework.response import Response


@pytest.mark.django_db
class TestVersionEndpoint:
    """Тесты version endpoint."""

    def setup_method(self):
        self.client = APIClient()
    
    def test_get_version(self):
        """Проверка endpoint версии."""
        response: Response = self.client.get('/version/')
        
        assert response.status_code == 200
        assert 'app_name' in response.data
        assert 'version' in response.data