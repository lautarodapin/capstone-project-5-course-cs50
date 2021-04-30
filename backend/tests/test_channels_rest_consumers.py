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

from backend.consumers import ChatConsumer, MessageConsumer
from backend.models import Chat, Message, User
from asyncio.exceptions import TimeoutError

application = URLRouter([
    re_path(r"^test/message/$", MessageConsumer.as_asgi()),
    re_path(r"^test/chat/$", ChatConsumer.as_asgi()),
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

@pytest.fixture
def basic_chats() -> Tuple[User, Chat, Chat, Chat]:
    user1 : User = User.objects.create_user(username="test1", password="testpassword123")
    user2 : User = User.objects.create_user(username="test2", password="testpassword123")
    chat_1 : Chat = Chat.objects.create()
    chat_2 : Chat = Chat.objects.create()
    chat_3 : Chat = Chat.objects.create()
    chat_1.members.add(user1.pk)
    chat_1.members.add(user2.pk)
    chat_1.save()
    chat_2.members.add(user1.pk)
    chat_2.members.add(user2.pk)
    chat_2.save()
    chat_3.members.add(user1.pk)
    chat_3.members.add(user2.pk)
    chat_3.save()
    return user1, chat_1, chat_2, chat_3

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_message_consumer_observer(basic_users: Tuple[User, User, Chat]):
    user_1, user_2, chat = basic_users
    communicator = AuthWebsocketCommunicator(application, "/test/message/", user=user_1)
    connected, subprotocol = await communicator.connect()
    assert connected

    communicator_2 = AuthWebsocketCommunicator(application, "/test/message/", user=user_2)
    connected, subprotocol = await communicator_2.connect()
    assert connected

    await communicator.send_json_to({
        "action": "subscribe_to_messages_in_chat",
        "chat": chat.pk,
        "request_id": now().timestamp(),
    })

    response = await communicator.receive_json_from()
    assert response["response_status"] == status.HTTP_200_OK

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

    # try:
    #     response = await communicator.receive_json_from()
    #     assert False
    # except TimeoutError:
    #     assert True

    # with pytest.raises(TimeoutError) as e_info:
    #     await communicator.receive_json_from()
    # assert str(e_info.value) == ""
    # Test join chat.
    await communicator.send_json_to({
        "action": "join_chat",
        "chat": chat.pk,
        "request_id": now().timestamp(),
    })
    response = await communicator.receive_json_from()
    assert response["status"] == status.HTTP_200_OK
    assert response["message"] == f"{user_1.username} joined the chat"


    # try:
    #     response = await communicator_2.receive_json_from()
    #     assert False
    # except TimeoutError:
    #     assert True

    await communicator_2.send_json_to({
        "action":"join_chat",
        "request_id": now().timestamp(),
        "chat": chat.pk,
    })
    response = await communicator.receive_json_from()
    assert response["action"] == "notification"
    assert response["action"] == "notification"
    assert response["message"] == f"{user_2.username} joined the chat"
    assert response["chat"] == chat.pk
    assert response["user"]["username"] == user_2.username
    assert response["user"]["id"] == user_2.pk
    assert response["status"] == status.HTTP_200_OK

    response = await communicator_2.receive_json_from()
    assert response["action"] == "notification"

    await communicator.disconnect()
    response = await communicator_2.receive_json_from()
    assert response["action"] == "notification"



@pytest.mark.skip("TODO fix test")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_chat_consumer_subscription(basic_chats: Tuple[User, Chat, Chat, Chat]):
    user, chat_1, chat_2, chat_3 = basic_chats

    communicator = AuthWebsocketCommunicator(application, "/test/chat/", user=user)
    connected, subprotocol = await communicator.connect()
    assert connected
    
    await communicator.send_json_to({
        "action": "subscribe_to_notifications",
        "request_id": now().timestamp(),
    })

    response = await communicator.receive_json_from()
    assert response["response_status"] == status.HTTP_201_CREATED
    assert response["action"] == "subscribe_to_notifications"
    
    await database_sync_to_async(Message.objects.create)(
        chat=chat_1,
        user=user,
        text="test"
    )
    response = await communicator.receive_json_from()
    assert response
    assert response["response_status"] == status.HTTP_201_CREATED
    assert response["data"]["text"] == "test"
    assert response["action"] == "notification"
    await database_sync_to_async(Message.objects.create)(
        chat=chat_2,
        user=user,
        text="test"
    )
    response = await communicator.receive_json_from()
    assert response
    assert response["response_status"] == status.HTTP_201_CREATED
    assert response["data"]["text"] == "test"
    assert response["action"] == "notification"
    await database_sync_to_async(Message.objects.create)(
        chat=chat_3,
        user=user,
        text="test"
    )
    response = await communicator.receive_json_from()
    assert response
    assert response["response_status"] == status.HTTP_201_CREATED
    assert response["data"]["text"] == "test"
    assert response["action"] == "notification"

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_subscribe_to_messages_in_chat_authentication(basic_chats: Tuple[User, Chat, Chat, Chat]):
    user, chat_1, chat_2, chat_3 = basic_chats

    communicator = AuthWebsocketCommunicator(application, "/test/message/")
    connected, subprotocol = await communicator.connect()
    assert connected
    
    await communicator.send_json_to({
        "action": "subscribe_to_messages_in_chat",
        "request_id": now().timestamp(),
        "chat": chat_1.pk,
    })

    response = await communicator.receive_json_from()
    assert response["response_status"] == status.HTTP_403_FORBIDDEN
    
    await communicator.disconnect()

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_subscribe_to_chat_notification_without_been_login(basic_chats: Tuple[User, Chat, Chat, Chat]):
    user, chat_1, chat_2, chat_3 = basic_chats

    communicator = AuthWebsocketCommunicator(application, "/test/chat/")
    connected, subprotocol = await communicator.connect()
    assert connected
    
    await communicator.send_json_to({
        "action": "subscribe_to_notifications",
        "request_id": now().timestamp(),
    })

    response = await communicator.receive_json_from()
    assert response["response_status"] == status.HTTP_403_FORBIDDEN
    assert response["action"] == "subscribe_to_notifications"
    
    await communicator.disconnect()