from typing import Tuple
import unittest
import pytest
import backend.signals
from channels.db import database_sync_to_async
from django.test import TestCase
from rest_framework import status
from channels.testing import HttpCommunicator
from channels.testing import ApplicationCommunicator
from channels.testing import WebsocketCommunicator
from .utils import AuthWebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path
from django.utils.timezone import now

from backend.consumers import MessageConsumer
from backend.models import Chat, Message, User
from asyncio import TimeoutError
application = URLRouter([
    re_path(r"^testws/$", MessageConsumer.as_asgi()),
])

@pytest.fixture
def basic_users()->Tuple[User, User, Chat]:
    user1 : User = User.objects.create_user(username="test1", password="testpassword123")
    user2 : User = User.objects.create_user(username="test2", password="testpassword123")
    chat : Chat = Chat.objects.create()
    chat.members.add(user1.pk)
    chat.members.add(user2.pk)
    chat.save()
    return user1, user2, chat


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_message_consumer_observer(basic_users: Tuple[User, User, Chat]):
    user_1, user_2, chat = basic_users
    communicator = AuthWebsocketCommunicator(application, "/testws/", user=user_1)
    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.send_json_to({
        "action": "subscribe_to_messages_in_chat",
        "chat": chat.pk,
        "request_id": now().timestamp(),
    })

    response = await communicator.receive_json_from()
    assert response["status"] == status.HTTP_200_OK

    message: Message = await database_sync_to_async(Message.objects.create)\
        (user=user_2, chat=chat, text="user 2 sends a message")
    response = await communicator.receive_json_from()
    assert response["action"] == "create"
    assert response["data"]["text"] == message.text
    assert response["data"]["user"]["id"] == user_2.pk
    assert response["data"]["chat"]["id"] == chat.pk


    # If a message is sent in another chat that isn't subscribed, it shouldn't
    # receive a message
    chat_2 : Chat = await database_sync_to_async(Chat.objects.create)()
    await database_sync_to_async(chat_2.members.add)(user_1.pk)
    await database_sync_to_async(chat_2.members.add)(user_2.pk)
    await database_sync_to_async(chat_2.save)()
    message: Message = await database_sync_to_async(Message.objects.create)\
        (user=user_2, chat=chat_2, text="user 2 sends a message")

    with pytest.raises(TimeoutError) as e_info:
        response = await communicator.receive_json_from()



    await communicator.disconnect()
