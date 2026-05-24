"""Тесты WebSocket для игровой сессии QuizSession."""
import pytest
import pytest_asyncio
from _pytest.fixtures import FixtureRequest
from typing import cast
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer, InMemoryChannelLayer
from sapere_aude.asgi import application
from app.models import QuizSession, Quiz
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async


@pytest.mark.asyncio
class TestQuizWebSocket:
    """
    Набор асинхронных тестов для WebSocket-соединений в рамках игровой сессии.
    """

    user: User
    quiz: Quiz
    session: QuizSession
    communicator1: WebsocketCommunicator
    communicator2: WebsocketCommunicator
    connected: bool

    @pytest_asyncio.fixture(autouse=True, loop_scope="function")
    async def create_test_data(self, request: FixtureRequest):
        """
        Фикстура, автоматически подключаемая к каждому тесту.
        """
        instance = cast(TestQuizWebSocket, request.instance)

        instance.user = await sync_to_async(User.objects.create_user)(
            username='testuser',
            password='testpass',
        )

        instance.quiz = await sync_to_async(Quiz.objects.create)(
            title="Вебсокетный квиз",
            created_by=instance.user,
        )

        instance.session = await sync_to_async(QuizSession.objects.create)(
            quiz=instance.quiz,
            session_code="WS123",
        )

        instance.communicator1 = WebsocketCommunicator(
            application=application,
            path=f"/ws/quiz/{instance.session.session_code}/",
        )
        instance.connected, _ = await instance.communicator1.connect()

        instance.communicator2 = WebsocketCommunicator(
            application=application,
            path=f"/ws/quiz/{instance.session.session_code}/",
        )
        connected, _ = await instance.communicator2.connect()

        yield

        await instance.communicator1.disconnect()
        await instance.communicator2.disconnect()

        await sync_to_async(instance.session.delete)()
        await sync_to_async(instance.quiz.delete)()
        await sync_to_async(instance.user.delete)()

    @pytest.mark.django_db()
    async def test_connect(self):
        """Проверка успешного установления WebSocket‑соединения."""
        assert self.connected is True

    @pytest.mark.django_db()
    async def test_broadcast_receive(self):
        """
        Проверка широковещательной рассылки сообщений всем участникам сессии.
        """
        channel_layer: InMemoryChannelLayer = get_channel_layer()

        await channel_layer.group_send(
            group=f"quiz_{self.session.session_code}",
            message={
                "type": "quiz_message",
                "message": "Start!",
            },
        )
        
        response = await self.communicator2.receive_json_from()

        assert response["message"] == "Start!"