from typing import Tuple
import unittest
import pytest
from channels.db import database_sync_to_async
from django.test import TestCase
from rest_framework import status
from channels.testing import HttpCommunicator
from channels.testing import ApplicationCommunicator
from channels.testing import WebsocketCommunicator
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
    user1, user2, chat = basic_users
    communicator = WebsocketCommunicator(application, "/testws/1/")  # /1/ means the PK=1 chat from the url
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to({
        "type":"chat_message",
        "message":"test message",
        "user":user1.pk,
    })
    response = await communicator.receive_json_from()
    assert response["status"] == status.HTTP_201_CREATED
    assert response["data"]["user"]["id"] == user1.pk

    await communicator.send_json_to({
        "type":"chat_message",
        "message":"test message",
        "user":user2.pk,
    })
    response = await communicator.receive_json_from()
    assert response["status"] == status.HTTP_201_CREATED
    assert response["data"]["user"]["id"] == user2.pk
    communicator.disconnect()

