from django.test import TestCase
from rest_framework.test import APIClient, RequestsClient
from rest_framework import status
from .serializers import *
class BasicTest(TestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.user: User = User.objects.create_user(username="test", password="testpassword123")
        return super().setUp()


    def test_create_user(self):
        response = self.client.post("/api/users/", {
            "username":"test_user",
            "password":"testpassword123",
        }, format="json")
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictContainsSubset({
            "username":"test_user",
            "chats":[],
        }, response.data)

    def test_user_detail_response(self):
        response = self.client.get("/api/users/1/")
        data = response.json()
        print("test_user_detail_response", response.status_code, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_list_response(self):
        response = self.client.get("/api/users/")
        print("test_user_list_response", response)
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(data["results"], list))
        self.assertEqual(len(data["results"]), 1)