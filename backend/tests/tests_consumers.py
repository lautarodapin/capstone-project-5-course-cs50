import unittest
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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decorator():
    user1 : User = User.objects.create_user(username="test1", password="testpassword123")
    user2 : User = User.objects.create_user(username="test2", password="testpassword123")
    chat : Chat = Chat.objects.create()
    chat.members.add(user1.pk)
    chat.members.add(user2.pk)
    chat.save()
    communicator = WebsocketCommunicator(application, "/testws/1/")
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to({
        "type":"chat_message",
        "message":"test message",
        "user":user1.pk,
    })
    response = await communicator.receive_from()
    assert response["status"] == 200