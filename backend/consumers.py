from typing import OrderedDict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.checks import messages
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import User, Message, Chat
from .serializers import MessageSerializer

import json


class ChatConsumer(AsyncWebsocketConsumer):

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
        return super().disconnect(code)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type_ = text_data_json.get("type")
        message = text_data_json.get("message")
        await self.channel_layer.group_send(
            self.room_group_name,
            text_data_json,
        )

    async def chat_message(self, event):
        event["data"] = await self.create_message(message=event["message"], user_id=event["user"])
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def create_message(self, message: str, user_id: int) -> ReturnDict:
        user: User = User.objects.get(pk=user_id)
        chat: Chat = Chat.objects.get(pk=self.room_name)
        message : Message = Message.objects.create(user=user, chat=chat, text=message)
        serializer = MessageSerializer(instance=message, many=False)
        return serializer.data