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

@pytest.mark.skip()
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator(basic_users: Tuple[User, User, Chat]):
    user_1, user_2, chat = basic_users
    comm_user_1 = AuthWebsocketCommunicator(application, "/testws/1/", user=user_1)  # /1/ means the PK=1 chat from the url
    connected, subprotocol = await comm_user_1.connect()
    assert connected

    comm_user_2 = AuthWebsocketCommunicator(application, "/testws/1/", user=user_2)  # /1/ means the PK=1 chat from the url
    connected, subprotocol = await comm_user_2.connect()
    assert connected

    # After the user 2 joins in, it sends a joined_chat that the user_1 should receive
    await comm_user_2.send_json_to({
        "type": "joined_chat",
        "user": user_2.pk,
    })
    response = await comm_user_1.receive_json_from()
    assert response
    assert response["from"] == user_2.pk
    assert response["chat"] == chat.pk
    assert response["message"] == f"User {user_2.username} join in the chat"
    
    # User 1 sends a message
    await comm_user_1.send_json_to({
        "type": "chat_message",
        "user": user_1.pk,
        "message": "user 1 sends a message",
    })

    # user 1 should receive the message
    # user 2 should receive a notification and then the message
    user_1_response = await comm_user_1.receive_json_from()
    user_2_response = await comm_user_2.receive_json_from()
    user_2_response_2 = await comm_user_2.receive_json_from()
    assert user_1_response["status"] == status.HTTP_201_CREATED
    assert user_1_response["user"] == user_1.pk
    
    assert  user_2_response["status"] == status.HTTP_200_OK
    assert  user_2_response["from"] == user_1.pk
    assert  user_2_response["chat"] == chat.pk
    assert  user_2_response["message"] == "user 1 sends a message"

    assert user_2_response_2["status"] == status.HTTP_201_CREATED
    assert user_2_response_2["user"] == user_1.pk


    await comm_user_1.disconnect()
    await comm_user_2.disconnect()
