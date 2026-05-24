"""Тесты для QuizViewSet list/retrieve/create/update/delete/start_session endpoints."""
import pytest
from rest_framework.test import APIClient
from rest_framework.response import Response
from django.contrib.auth.models import User
from app.models import Quiz, QuizSession


@pytest.mark.django_db
class TestQuizListEndpoint:
    """Тесты endpoint списка квизов."""
    
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
    
    def test_list_quizzes(self):
        """Проверка получения списка квизов."""
        response: Response = self.client.get('/api/v1/quizzes/')

        assert response.status_code == 200
        assert len(response.data['results']) == 2
    
    def test_list_quizzes_pagination(self):
        """Проверка пагинации (10 квизов на страницу)."""
        response: Response = self.client.get('/api/v1/quizzes/')

        assert 'count' in response.data
        assert 'results' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
    
    def test_filter_by_is_active(self):
        """Проверка фильтрации по is_active."""
        response: Response = self.client.get('/api/v1/quizzes/?is_active=true')

        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Тестовый квиз 1'
    
    def test_search_by_title(self):
        """Проверка поиска по title."""
        response: Response = self.client.get('/api/v1/quizzes/?search=Тестовый квиз 1')

        assert response.status_code == 200
        assert len(response.data['results']) == 1
    
    def test_ordering_by_created_at(self):
        """Проверка сортировки по created_at."""
        response: Response = self.client.get('/api/v1/quizzes/?ordering=-created_at')

        assert response.status_code == 200
        assert response.data['results'][0]['id'] >= response.data['results'][1]['id']


@pytest.mark.django_db
class TestQuizRetrieveEndpoint:
    """Тесты endpoint детальной информации о квизе."""
    
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
    
    def test_retrieve_quiz(self):
        """Проверка получения детальной информации о квизе."""
        response: Response = self.client.get(f'/api/v1/quizzes/{self.quiz.id}/')

        assert response.status_code == 200
        assert response.data['title'] == 'Тестовый квиз'
        assert response.data['description'] == 'Описание квиза'
    
    def test_retrieve_nonexistent_quiz(self):
        """Проверка получения несуществующего квиза."""
        response: Response = self.client.get('/api/v1/quizzes/99999/')

        assert response.status_code == 404
    
    def test_retrieve_quiz_with_questions(self):
        """Проверка что квиз содержит вложенные вопросы."""
        response: Response = self.client.get(f'/api/v1/quizzes/{self.quiz.id}/')

        assert response.status_code == 200
        assert 'questions' in response.data


@pytest.mark.django_db
class TestQuizCreateEndpoint:
    """Тесты endpoint создания квизов."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_quiz(self):
        """Проверка простого создания квиза."""
        payload = {
            "title": "Новый квиз",
            "description": "Тест",
            'questions': [
                {
                    'text': 'Первый вопрос',
                    'order': 1,
                    'timer_seconds': 30,
                },
            ],
        }

        response: Response = self.client.post(
            '/api/v1/quizzes/', payload, format='json',
        )

        assert response.status_code == 201
        assert Quiz.objects.filter(title="Новый квиз").exists()

    def test_create_quiz_no_questions(self):
        """Проверка, что квиз без вопросов не может быть создан."""
        payload = {
            "title": "Новый квиз",
            "description": "Тест",
        }

        response: Response = self.client.post(
            '/api/v1/quizzes/', payload, format='json',
        )

        assert response.status_code == 400
        assert not Quiz.objects.filter(title='Новый квиз').exists()

    def test_create_quiz_empty_questions(self):
        """Проверка, что квиз с пустым списком вопросов не может быть создан."""
        payload = {
            "title": "Новый квиз",
            "description": "Тест",
            'questions': [],
        }

        response: Response = self.client.post(
            '/api/v1/quizzes/', payload, format='json',
        )

        assert response.status_code == 400
        assert not Quiz.objects.filter(title="Новый квиз").exists()
    
    def test_anon_cant_create_quiz(self):
        """Проверка, что неавторизованный пользователь не может создать квиз."""
        payload = {
            "title": "Новый квиз",
            "description": "Тест",
        }

        anon_client = APIClient()
        response: Response = anon_client.post(
            '/api/v1/quizzes/', payload, format='json',
        )

        assert response.status_code == 403
        assert not Quiz.objects.filter(title="Новый квиз").exists()

    def test_create_quiz_with_not_enough_data(self):
        """Проверка, что квиз не создаться, если недостаточно данных."""
        payload = {
            "description": "Тест",
        }

        response: Response = self.client.post(
            '/api/v1/quizzes/', payload, format='json',
        )

        assert response.status_code == 400

    def test_create_quiz_with_empty_title(self):
        """Проверка, что квиз не создаться, если title пуст данных."""
        payload = {
            "title": "",
            "description": "Тест",
        }

        response: Response = self.client.post(
            '/api/v1/quizzes/', payload, format='json',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestQuizUpdateEndpoint:
    """Тесты endpoint обновления информации о квизе."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)
        
        self.quiz = Quiz.objects.create(
            title='Тестовый квиз',
            description='Описание квиза',
            created_by=self.user1,
            is_active=True,
        )
    
    def test_update_quiz(self):
        """Проверка обновления информации о квизе."""
        payload = {
            "title": "Обновленный заголовок",
        }

        response: Response = self.client1.put(
            f'/api/v1/quizzes/{self.quiz.id}/', payload, format='json',
        )

        assert response.status_code == 200
        assert Quiz.objects.get(id=self.quiz.id).title == "Обновленный заголовок"
    
    def test_update_nonexistent_quiz(self):
        """Проверка обновления несуществующего квиза."""
        payload = {
            "title": "Обновленный заголовок",
        }

        response: Response = self.client1.put(
            '/api/v1/quizzes/99999/', payload, format='json',
        )

        assert response.status_code == 404

    def test_anon_cant_update_quiz(self):
        """Проверка, что неавторизованный пользователь не может обновить квиз."""
        payload = {
            "title": "Обновленный заголовок",
        }

        anon_client = APIClient()
        response: Response = anon_client.put(
            f'/api/v1/quizzes/{self.quiz.id}/', payload, format='json',
        )

        assert response.status_code == 403
        assert not Quiz.objects.get(id=self.quiz.id).title == "Обновленный заголовок"

    def test_update_quiz_with_not_enough_data(self):
        """Проверка, что квиз не обновится, если недостаточно данных."""
        payload = {}

        response: Response = self.client1.put(
            f'/api/v1/quizzes/{self.quiz.id}/', payload, format='json',
        )

        assert response.status_code == 400
        assert Quiz.objects.get(id=self.quiz.id).title == "Тестовый квиз"

    def test_update_quiz_with_empty_title(self):
        """Проверка, что квиз не обновится, если title пуст данных."""
        payload = {
            "title": "",
        }

        response: Response = self.client1.put(
            f'/api/v1/quizzes/{self.quiz.id}/', payload, format='json',
        )

        assert response.status_code == 400
        assert not Quiz.objects.get(id=self.quiz.id).title == ""

    def test_another_user_cant_update_quiz(self):
        """Проверка, что другой пользователь не может обновить чужой квиз."""
        payload = {
            "title": "Обновленный заголовок",
        }

        response: Response = self.client2.put(
            f'/api/v1/quizzes/{self.quiz.id}/', payload, format='json',
        )

        assert response.status_code == 403
        assert not Quiz.objects.get(id=self.quiz.id).title == "Обновленный заголовок"


@pytest.mark.django_db
class TestQuizDeleteEndpoint:
    """Тесты endpoint удаления информации о квизе."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
        )

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)
        
        self.quiz = Quiz.objects.create(
            title='Тестовый квиз',
            description='Описание квиза',
            created_by=self.user1,
            is_active=True,
        )
    
    def test_delete_quiz(self):
        """Проверка удаления квиза."""
        response: Response = self.client1.delete(f'/api/v1/quizzes/{self.quiz.id}/')

        assert response.status_code == 204
        assert not Quiz.objects.filter(id=self.quiz.id).exists()
    
    def test_delete_nonexistent_quiz(self):
        """Проверка удаления несуществующего квиза."""
        response: Response = self.client1.delete('/api/v1/quizzes/99999/')

        assert response.status_code == 404

    def test_anon_cant_delete_quiz(self):
        """Проверка, что неавторизованный пользователь не может удалить квиз."""
        anon_client = APIClient()
        response: Response = anon_client.delete(f'/api/v1/quizzes/{self.quiz.id}/')

        assert response.status_code == 403
        assert Quiz.objects.filter(id=self.quiz.id).exists()

    def test_another_user_cant_delete_quiz(self):
        """Проверка, что другой пользователь не может удалить чужой квиз."""
        response: Response = self.client2.delete(f'/api/v1/quizzes/{self.quiz.id}/')

        assert response.status_code == 403
        assert Quiz.objects.filter(id=self.quiz.id).exists()


@pytest.mark.django_db
class TestQuizStartSessionEndpoint:
    """Тесты endpoint начала игровой сессии."""
    
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

    def test_start_session(self):
        """Проверка начала игровой сессии."""
        response: Response = self.client.post(f'/api/v1/quizzes/{self.quiz.id}/start_session/')

        assert response.status_code in (200, 201)
        assert 'session_code' in response.data
        assert QuizSession.objects.filter(session_code=response.data['session_code']).exists()

    def test_start_session_nonexistent_quiz(self):
        """Тест на запрос с несуществующим ID квиза."""
        response: Response = self.client.post(f'/api/v1/quizzes/99999/start_session/')

        assert response.status_code == 404

    def test_anon_cant_start_session(self):
        """Проверка, что неавторизованный пользователь не начать игровую сессию."""
        anon_client = APIClient()
        response: Response = anon_client.delete(f'/api/v1/quizzes/{self.quiz.id}/start_session/')

        assert response.status_code == 403
        assert Quiz.objects.filter(id=self.quiz.id).exists()