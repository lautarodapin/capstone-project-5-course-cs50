from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token

from .models import (User, Chat, Message)

class MessageSerializer(ModelSerializer):

    class Meta:
        model = Message
        depth = 2
        fields = ["id", "user", "chat", "text", "created_at", "mod_at",]


class ChatSerializer(ModelSerializer):

    class Meta:
        model = Chat
        depth = 2
        fields = ["id", "members", "is_group", "chat_name", "messages", "created_at", "mod_at", ]


class UserSerializer(ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        depth = 2
        fields = ["id", "username", "password", "last_login", "token", "chats", "messages",]
        extra_kwargs = {
            'password': {'write_only': True},
            'last_login': {'read_only': True},
        }

    def get_token(self, obj:User):
        return obj.auth_token.key
        
    def validate_password(self, value):
        user = self.context["request"].user
        validate_password(password=value, user=user)