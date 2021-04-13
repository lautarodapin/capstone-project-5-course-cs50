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

class MyTests(TestCase):
    databases = {"default", "test"}

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user1 : User = User.objects.create_user(username="test1", password="testpassword123")
        cls.user2 : User = User.objects.create_user(username="test2", password="testpassword123")
        cls.chat : Chat = Chat.objects.create()
        cls.chat.members.add(cls.user1.pk)
        cls.chat.members.add(cls.user2.pk)
        cls.chat.save()
        return super().setUpTestData()

    def setUp(self) -> None:
        return super().setUp()

    async def test_my_consumer(self):
        communicator = WebsocketCommunicator(application, "/testws/1/")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        #  TODO no usa la base de datos test el consumer
        await communicator.send_json_to({
            "type":"chat_message",
            "message":"test message",
            "user":self.user1.pk,
        })
        response = await communicator.receive_from()
        self.assertEqual(response["status"], 200)

