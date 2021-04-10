from django.test import TestCase
from rest_framework.test import APIClient

from .serializers import *
class BasicTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()

        self.user1 : User = User.objects.create(username="user1", password="test12345678")
        self.user2 : User = User.objects.create(username="user2", password="test12345678")
        self.user3 : User = User.objects.create(username="user3", password="test12345678")
        self.chat1 : Chat = Chat.objects.create()
        self.chat1.members.add(self.user1)
        self.chat1.members.add(self.user2)
        self.chat2 : Chat = Chat.objects.create()
        self.chat2.members.add(self.user1)
        self.chat2.members.add(self.user2)
        self.chat2.members.add(self.user3)
        
        return super().setUp()

    def test_user_serializer(self):
        serializer = UserSerializer(instance=self.user1, many=False)
        data = dict(dict(serializer.data))
        self.assertEqual(data["username"], "user1")
        self.assertEqual(data["chats"][0]["id"], 1)
        self.assertEqual(data["chats"][1]["id"], 2)