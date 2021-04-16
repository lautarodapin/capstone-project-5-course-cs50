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

from backend.consumers import ChatConsumer
from backend.models import Chat, User

application = URLRouter([
    re_path(r"^testws/(?P<chat_id>\w+)/$", ChatConsumer.as_asgi()),
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
async def test_decorator(basic_users: Tuple[User, User, Chat]):
    # 1.
    user_1, user_2, chat = basic_users
    comm_user_1 = AuthWebsocketCommunicator(application, "/testws/1/", user=user_1)  # /1/ means the PK=1 chat from the url
    connected, subprotocol = await comm_user_1.connect()
    assert connected

    # 2.
    await comm_user_1.send_json_to({
        "type": "joined_chat",
        "from": user_1.pk,
        "chat": chat.pk,
    })
    
    # 4.
    comm_user_2 = AuthWebsocketCommunicator(application, "/testws/1/", user=user_2)  # /1/ means the PK=1 chat from the url
    connected, subprotocol = await comm_user_2.connect()
    assert connected

    response = await comm_user_2.receive_json_from()
    assert response["status"] == status.HTTP_200_OK
    assert response["type"] == "notification"
    assert response["from"] == user_1.pk
    assert response["chat"] == chat.pk
    assert response["message"] == f"User {user_1.username} join in the chat"

    # 5.
    await comm_user_2.send_json_to({
        "type": "joined_chat",
        "from": user_2.pk,
        "chat": chat.pk,
    })

    # 6.
    response_user_1 = await comm_user_1.receive_json_from()
    assert response_user_1["status"] == status.HTTP_200_OK
    assert response_user_1["type"] == "notification"
    assert response_user_1["from"] == user_2.pk
    assert response_user_1["chat"] == chat.pk

    # 7.
    await comm_user_1.send_json_to({
        "type": "chat_message",
        "from": user_1.pk,
        "message": "user 1 sends a message",
        "chat": chat.pk,
    })

    # 9.
    response_user_1 = await comm_user_1.receive_json_from()
    response_user_2 = await comm_user_2.receive_json_from()
    assert response_user_1["type"] == "chat_message"
    assert response_user_1["status"] == status.HTTP_201_CREATED
    assert response_user_1["message"] == "user 1 sends a message"
    assert response_user_1["from"] == user_1.pk
    assert response_user_1["chat"] == chat.pk

    assert response_user_2["type"] == "chat_message"
    assert response_user_2["status"] == status.HTTP_201_CREATED
    assert response_user_2["message"] == "user 1 sends a message"
    assert response_user_2["from"] == user_1.pk
    assert response_user_2["chat"] == chat.pk

    # 8.
    response_user_2_notification = await comm_user_2.receive_json_from()
    assert response_user_2_notification["type"] == "notification"
    assert response_user_2_notification["message"] == "user 1 sends a message"
    assert response_user_2_notification["from"] == user_1.pk
    assert response_user_2_notification["chat"] == chat.pk


    await comm_user_1.disconnect()
    await comm_user_2.disconnect()
