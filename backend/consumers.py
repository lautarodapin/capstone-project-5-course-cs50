from typing import OrderedDict
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

@pytest.mark.django_db(transaction=True)
class ChatConsumer(AsyncJsonWebsocketConsumer):


    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["chat_id"]
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
        type_ = content.get("type")
        if type_ not in ["chat_message"]:
            return 
        message = content.get("message")
        await self.channel_layer.group_send(
            self.room_group_name,
            content,
        )
    async def notification(self, event):
        event["status"] = status.HTTP_200_OK
        await self.send_json(event)

    async def chat_message(self, event):
        print(event)
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