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
    user_1, user_2, chat = basic_users
    comm_user_1 = AuthWebsocketCommunicator(application, "/testws/1/", user=user_1)  # /1/ means the PK=1 chat from the url
    connected, subprotocol = await comm_user_1.connect()
    assert connected

    comm_user_2 = AuthWebsocketCommunicator(application, "/testws/1/", user=user_2)  # /1/ means the PK=1 chat from the url
    connected, subprotocol = await comm_user_2.connect()
    assert connected

    # After the user 2 joins in, user 1 should receive a notification
    response = await comm_user_1.receive_json_from()
    assert response
    assert response["from"] == user_2.pk
    assert response["chat"] == str(chat.pk)
    assert response["message"] == f"User {user_2.username} join in the chat"
    

    await comm_user_1.disconnect()
    await comm_user_2.disconnect()
