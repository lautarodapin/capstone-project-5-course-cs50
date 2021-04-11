from django.test import TestCase
from rest_framework.test import APIClient, RequestsClient
from rest_framework import status
from .serializers import *
class BasicTest(TestCase):

    def setUp(self) -> None:
        self.client = RequestsClient()
        return super().setUp()


    def test_create_user(self):
        response = self.client.post("http://localhost:8000/api/users/", {
            "username":"test_user",
            "password":"testpassword123",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)