import json
import logging
import pytest
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
logger = logging.getLogger(__name__)
class SessionGroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'session_{self.session_id}'
        self._in_group = False
        await self.add_to_group()
        await self.accept()
    async def disconnect(self, close_code):
        await self.remove_from_group()
    async def receive(self, text_data):
        pass
    async def add_to_group(self):
        if not self._in_group:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            self._in_group = True
            logger.info(f"Подписка: канал {self.channel_name} добавлен в группу {self.group_name}")
        else:
            logger.warning(f"Повторная подписка: канал {self.channel_name} уже в группе {self.group_name}")
    async def remove_from_group(self):
        if self._in_group:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            self._in_group = False
            logger.info(f"Отписка: канал {self.channel_name} удален из группы {self.group_name}")
        else:
            logger.warning(f"Попытка повторного удаления: канал {self.channel_name} уже вне группы {self.group_name}")
    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps(event))
@pytest.mark.asyncio
async def test_add_and_remove_group():
    channel_layer = get_channel_layer()
    group_name = 'session_test'
    channel_name = 'test_channel_1'
    await channel_layer.group_add(group_name, channel_name)
    groups = await channel_layer.group_channels(group_name)
    assert channel_name in groups
    await channel_layer.group_discard(group_name, channel_name)
    groups = await channel_layer.group_channels(group_name)
    assert channel_name not in groups
@pytest.mark.asyncio
async def test_consumer_add_method():
    consumer = SessionGroupConsumer()
    consumer.channel_layer = get_channel_layer()
    consumer.channel_name = 'test_channel_2'
    consumer.group_name = 'session_test_2'
    consumer._in_group = False
    await consumer.add_to_group()
    # Проверяем, что _in_group стал True
    assert consumer._in_group is True
    await consumer.add_to_group()
@pytest.mark.asyncio
async def test_consumer_remove_method():
    consumer = SessionGroupConsumer()
    consumer.channel_layer = get_channel_layer()
    consumer.channel_name = 'test_channel_3'
    consumer.group_name = 'session_test_3'
    consumer._in_group = True
    await consumer.remove_from_group()
    assert consumer._in_group is False
    await consumer.remove_from_group()