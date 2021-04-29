from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework.authtoken.models import Token

from .models import (MessageNotification, User, Chat, Message)


class ChatSerializer(ModelSerializer):

    class Meta:
        model = Chat
        depth = 1
        fields = ["id", "members", "is_group", "chat_name", "messages", "created_at", "mod_at", ]


class UserSerializer(ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        depth = 1
        fields = ["id", "username", "password", "last_login", "token", "chats", ]
        extra_kwargs = {
            'password': {'write_only': True},
            'last_login': {'read_only': True},
        }

    def get_token(self, obj:User):
        return obj.auth_token.key
        
    def validate_password(self, value):
        user = self.context["request"].user
        validate_password(password=value, user=user)

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class MessageSerializer(ModelSerializer):

    class Meta:
        model = Message
        fields = ["id", "user", "chat", "text", "created_at", "mod_at",]

    def to_representation(self, instance : Message):
        data = super().to_representation(instance)
        data["user"] = UserSerializer(instance.user).data
        data["chat"] = ChatSerializer(instance.chat).data
        return data


class MessageNotificationSerializer(ModelSerializer):
    class Meta:
        model = MessageNotification
        fields = [
            "id",
            "from_user",
            "user",
            "chat",
            "message",
            "text",
            "is_read",
            "read_time",
        ]
        extra_kwargs = {
            "from_user": {"read_only": True, },
            "user": {"read_only": True, },
            "chat": {"read_only": True, },
            "message": {"read_only": True, },
        }

    def to_representation(self, instance: MessageNotification):
        data = super().to_representation(instance)
        data["from_user"] = UserSerializer(instance.from_user).data
        data["user"] = UserSerializer(instance.user).data
        data["chat"] = ChatSerializer(instance.chat).data
        data["message"] = MessageSerializer(instance.message).data
        return data