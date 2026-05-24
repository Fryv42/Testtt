"""Тесты Observer pattern для WebSocket-групп."""
import pytest
from channels.layers import get_channel_layer

from app.observer_pattern import SessionGroupConsumer


@pytest.mark.asyncio
async def test_add_and_remove_group():
    channel_layer = get_channel_layer()
    group_name = 'session_test'
    channel_name = 'test_channel_1'
    await channel_layer.group_add(group_name, channel_name)
    await channel_layer.group_discard(group_name, channel_name)


@pytest.mark.asyncio
async def test_consumer_add_method():
    consumer = SessionGroupConsumer()
    consumer.channel_layer = get_channel_layer()
    consumer.channel_name = 'test_channel_2'
    consumer.group_name = 'session_test_2'
    consumer._in_group = False
    await consumer.add_to_group()
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
