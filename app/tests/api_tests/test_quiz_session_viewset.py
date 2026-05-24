"""Тесты для QuizSessionViewSet list/retrieve/join endpoints."""
import pytest
from rest_framework.test import APIClient
from rest_framework.response import Response
from django.contrib.auth.models import User
from app.models import Quiz, QuizSession, Participant


@pytest.mark.django_db
class TestQuizSessionListEndpoint:
    """Тесты endpoint списка сессий квизов."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.quiz1 = Quiz.objects.create(
            title='Тестовый квиз 1',
            description='Описание 1',
            created_by=self.user,
            is_active=True,
        )
        self.quiz2 = Quiz.objects.create(
            title='Тестовый квиз 2',
            description='Описание 2',
            created_by=self.user,
            is_active=False,
        )

        self.session1 = QuizSession.objects.create(
            quiz=self.quiz1,
            session_code='Sess1',
            is_active=True,
        )
        self.session2 = QuizSession.objects.create(
            quiz=self.quiz2,
            session_code='Sess2',
            is_active=False,
        )
    
    def test_list_sessions(self):
        """Проверка получения списка сессий."""
        response: Response = self.client.get('/api/v1/sessions/')

        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_list_sessions_pagination(self):
        """Проверка пагинации (10 сессий на страницу)."""
        response: Response = self.client.get('/api/v1/sessions/')

        assert 'count' in response.data
        assert 'results' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
    
    def test_filter_by_is_active(self):
        """Проверка фильтрации по is_active."""
        response: Response = self.client.get('/api/v1/sessions/?is_active=true')

        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['session_code'] == 'Sess1'
    
    def test_search_by_session_code(self):
        """Проверка поиска по session code."""
        response: Response = self.client.get('/api/v1/sessions/?search=Sess1')

        assert response.status_code == 200
        assert len(response.data['results']) == 1


@pytest.mark.django_db
class TestQuizSessionRetrieveEndpoint:
    """Тесты endpoint детальной информации о игровой сессии."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.quiz = Quiz.objects.create(
            title='Тестовый квиз',
            description='Описание квиза',
            created_by=self.user,
            is_active=True,
        )

        self.session = QuizSession.objects.create(
            quiz=self.quiz,
            session_code='Sess',
            is_active=True,
        )
    
    def test_retrieve_session(self):
        """Проверка получения детальной информации о игровой сессии."""
        response: Response = self.client.get(f'/api/v1/sessions/{self.session.id}/')

        assert response.status_code == 200
        assert response.data['session_code'] == 'Sess'
        assert response.data['quiz_title'] == 'Тестовый квиз'
    
    def test_retrieve_nonexistent_session(self):
        """Проверка получения несуществующей игровой сессии."""
        response: Response = self.client.get('/api/v1/sessions/99999/')

        assert response.status_code == 404


@pytest.mark.django_db
class TestQuizSessionJoinEndpoint:
    """Тесты endpoint входа в игровую сессию."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser1',
            password='testpass123',
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.quiz = Quiz.objects.create(
            title='Тестовый квиз',
            description='Описание квиза',
            created_by=self.user,
            is_active=True,
        )

        self.session1 = QuizSession.objects.create(
            quiz=self.quiz,
            session_code='Sess1',
            is_active=True,
        )

        self.session2 = QuizSession.objects.create(
            quiz=self.quiz,
            session_code='Sess2',
            is_active=False,
        )

        Participant.objects.create(
            session=self.session1,
            name='Игрок123',
        )
        self.session1.refresh_from_db()

    def test_start_session(self):
        """Проверка присоединения участника к активной сессии."""
        payload = {
            'name': 'Игрок',
        }

        response: Response = self.client.post(f'/api/v1/sessions/{self.session1.id}/join/', payload)

        assert response.status_code == 200
        assert Participant.objects.filter(session=self.session1, name='Игрок').exists()
        assert response.data['name'] == 'Игрок'

    def test_join_requires_active_session(self):
        """Проверка, что нельзя присоединиться к неактивной сессии."""
        payload = {
            'name': 'Игрок',
        }

        response: Response = self.client.post(f'/api/v1/sessions/{self.session2.id}/join/', payload)

        assert response.status_code == 400

    def test_join_name_must_be_unique_within_session(self):
        """Проверка, что имя участника должно быть уникальным внутри одной сессии."""
        payload = {
            'name': 'Игрок123',
        }

        response: Response = self.client.post(f'/api/v1/sessions/{self.session1.id}/join/', payload)

        assert response.status_code == 400

    def test_join_session_nonexistent_quiz(self):
        """Тест на запрос с несуществующим ID игровой сессии."""
        payload = {
            'name': 'Игрок',
        }

        response: Response = self.client.post(f'/api/v1/sessions/99999/join/', payload)

        assert response.status_code == 404

    def test_anon_cant_join_session(self):
        """Проверка, что неавторизованный пользователь не начать игровую сессию."""
        anon_client = APIClient()

        payload = {
            'name': 'Игрок',
        }


        response: Response = anon_client.delete(f'/api/v1/sessions/{self.session1.id}/join/', payload)

        assert response.status_code == 403
        assert not Participant.objects.filter(session=self.session1, name='Игрок').exists()