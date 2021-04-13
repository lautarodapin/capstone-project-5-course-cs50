from django.test import TestCase
from rest_framework.test import APIClient, RequestsClient
from rest_framework import status
from backend.serializers import *
class BasicTest(TestCase):
    # databases = ["te"]
    def setUp(self) -> None:
        self.client = APIClient()
        self.user1: User = User.objects.create_user(username="test1", password="testpassword123")
        self.user2: User = User.objects.create_user(username="test2", password="testpassword123")
        return super().setUp()


    def test_create_user(self):
        response = self.client.post("/api/users/", {
            "username":"test_user",
            "password":"testpassword123",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictContainsSubset({
            "username":"test_user",
            "chats":[],
        }, response.data)

    def test_user_detail_response(self):
        response = self.client.get("/api/users/1/")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_list_response(self):
        response = self.client.get("/api/users/")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(data["results"], list))
        self.assertEqual(len(data["results"]), 2)


    def test_user1_create_chat_with_user2(self):
        self.client.login(username=self.user1.username, password="testpassword123")
        response = self.client.post(
            "/api/chats/create_chat_with/", 
            {
                "members":[self.user1.pk, self.user2.pk],
            },
            format="json",
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["members"].__len__(), 2)
        self.assertEqual(data["members"][0]["id"], 1)
        self.assertEqual(data["members"][1]["id"], 2)
        self.client.logout()

    def test_user1_create_chat_with_user2_that_already_exists(self):
        self.client.login(username=self.user1.username, password="testpassword123")
        chat:Chat = Chat.objects.create()
        chat.members.add(self.user1.pk)
        chat.members.add(self.user2.pk)
        chat.save()
        response = self.client.post(
            "/api/chats/create_chat_with/", 
            {
                "members":[self.user1.pk, self.user2.pk],
            },
            format="json",
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["members"].__len__(), 2)
        self.assertEqual(data["members"][0]["id"], 1)
        self.assertEqual(data["members"][1]["id"], 2)
        self.client.logout()

    def test_messages_in_chat_1(self):
        self.client.login(username=self.user1.username, password="testpassword123")
        chat:Chat = Chat.objects.create()
        chat.members.add(self.user1.pk)
        chat.members.add(self.user2.pk)
        Message.objects.create(user=self.user1, chat=chat, text="message 1")
        Message.objects.create(user=self.user2, chat=chat, text="message 2")
        response = self.client.get(f"/api/messages/messages_in_chat/?chat_id={chat.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["results"].__len__(), 2)
        self.assertEqual(data["results"][0]["id"], 1)
        self.assertEqual(data["results"][1]["id"], 2)
        self.client.logout()


    def test_current_user_login(self):
        response = self.client.get("/api/current-user/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.client.login(username=self.user1.username, password="testpassword123")
        response = self.client.get("/api/current-user/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.logout()


    