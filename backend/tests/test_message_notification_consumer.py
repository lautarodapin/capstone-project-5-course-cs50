from typing import Tuple
import unittest
import backend.signals
import pytest
from channels.db import database_sync_to_async
from django.test import TestCase
from .utils import AuthWebsocketCommunicator
from rest_framework import status
from channels.testing import HttpCommunicator
from channels.testing import ApplicationCommunicator
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import re_path

from backend.consumers import MessageNotificationConsumer
from backend.models import Chat, Message, User

application = URLRouter([
    re_path(r"^testws/$", MessageNotificationConsumer.as_asgi()),
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
async def test_notification_sent_after_creating_message(basic_users: Tuple[User, User, Chat]):
    user_1, user_2, chat = basic_users
    communicator = AuthWebsocketCommunicator(application, "/testws/", user=user_2)
    connected, subprotocol = await communicator.connect()
    assert connected
    
    await communicator.send_json_to(dict(
        action="subscribe_to_notifications",
        request_id=1,
    ))
    response = await communicator.receive_json_from()
    print(response)
    assert response["response_status"] == status.HTTP_201_CREATED

    message : Message = await database_sync_to_async(Message.objects.create)(
        user=user_1,
        chat=chat,
        text="user 1 sends a message to user 2",
    )

    response = await communicator.receive_json_from()
    print(response)
    assert response["response_status"] == status.HTTP_201_CREATED
    assert response["data"]["from_user"]["username"] == user_1.username
    assert response["data"]["user"]["username"] == user_2.username
    assert response["data"]["chat"]["id"] == chat.pk
    assert response["data"]["text"] == message.text
    assert response["data"]["is_read"] == False
    assert response["data"]["read_time"] == None


    await communicator.send_json_to(dict(
        action="mark_as_read",
        request_id=1,
        pk=message.message_notification.pk,
    ))

    response = await communicator.receive_json_from()
    print(response)
    assert response
    assert response["response_status"] == status.HTTP_200_OK
    assert response["data"]["is_read"] == True
    assert response["data"]["read_time"] is not None

    await communicator.disconnect()