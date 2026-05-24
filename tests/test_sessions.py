import pytest
from django.urls import reverse
from rest_framework import status


def _session_results(response):
    data = response.data
    if isinstance(data, list):
        return data
    return data.get('results', data)


@pytest.mark.django_db
def test_get_sessions_list(api_client, quiz_session):
    url = reverse('quizsession-list')
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    results = _session_results(response)
    assert len(results) > 0


@pytest.mark.django_db
def test_filter_active_sessions(api_client, quiz_session):
    url = f"{reverse('quizsession-list')}?is_active=true"
    response = api_client.get(url)
    results = _session_results(response)
    assert all(item['is_active'] for item in results)