"""WebSocket consumer для групповых событий сессии (Observer pattern)."""
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class SessionGroupConsumer(AsyncWebsocketConsumer):
    """Подписка канала на группу событий сессии."""

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'session_{self.session_id}'
        self._in_group = False
        await self.add_to_group()
        await self.accept()

    async def disconnect(self, code):
        await self.remove_from_group()

    async def receive(self, text_data=None, bytes_data=None):
        del text_data, bytes_data

    async def add_to_group(self):
        if not self._in_group:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            self._in_group = True
            logger.info(
                'Подписка: канал %s добавлен в группу %s',
                self.channel_name,
                self.group_name,
            )
        else:
            logger.warning(
                'Повторная подписка: канал %s уже в группе %s',
                self.channel_name,
                self.group_name,
            )

    async def remove_from_group(self):
        if self._in_group:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            self._in_group = False
            logger.info(
                'Отписка: канал %s удален из группы %s',
                self.channel_name,
                self.group_name,
            )
        else:
            logger.warning(
                'Попытка повторного удаления: канал %s уже вне группы %s',
                self.channel_name,
                self.group_name,
            )

    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps(event))
