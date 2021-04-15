from logging import getLogger
from typing import Dict, OrderedDict, Union
import pytest
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.checks import messages
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework import status
from .models import User, Message, Chat
from .serializers import MessageSerializer
from channels.exceptions import RequestAborted
import json

logger = getLogger(__name__)

@pytest.mark.django_db(transaction=True)
class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["chat_id"]
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        return await super().disconnect(code)

    async def receive_json(self, content):
        print("Receive_json", content)
        type_ = content.get("type")
        if type_ not in ["chat_message", "notification", "joined_chat"]:
            return 
        # message = content.get("message")
        await self.channel_layer.group_send(
            self.room_group_name,
            content,
        )

    async def joined_chat(self, event):
        # Joined chat notification.
        user : User = await self.get_user(event["user"])
        notification = self.create_notification(message=f"User {user.username} join in the chat")
        print(f"Joined chat {notification}")
        await self.channel_layer.group_send(
            self.room_group_name,
            notification
        )

    def create_notification(self, message: str) -> Dict[str, Union[str, int]]:
        return {
            "type": "notification",
            "message": message,
            "chat": int(self.chat_id),
            "from": self.scope["user"].pk,
        }

    async def notification(self, event):
        print("notification", event)
        if self.scope["user"].pk == event["from"]:  # Prevents from notifiying itself.
            return
        event["status"] = status.HTTP_200_OK
        await self.send_json(event)

    async def chat_message(self, event):
        print("chat_message", event)
        event["data"] = await self.create_message(message=event["message"], user_id=event["user"])
        event["status"] = status.HTTP_201_CREATED
        await self.send_json(event)


    @database_sync_to_async
    def create_message(self, message: str, user_id: int) -> ReturnDict:
        user: User = User.objects.get(pk=user_id)
        chat: Chat = Chat.objects.get(pk=self.room_name)
        message : Message = Message.objects.create(user=user, chat=chat, text=message)
        serializer = MessageSerializer(instance=message, many=False)
        return serializer.data

    @database_sync_to_async
    def get_user(self, pk: int) -> User:
        return User.objects.get(pk=pk)