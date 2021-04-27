from logging import getLogger
from typing import Dict, Optional, OrderedDict, Union
from django.db.models import query
import pytest
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import SyncToAsync, sync_to_async
from django.core.checks import messages
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework import status
from .models import User, Message, Chat
from .serializers import MessageSerializer, UserSerializer, ChatSerializer
from channels.exceptions import RequestAborted

from channelsmultiplexer.demultiplexer import AsyncJsonWebsocketDemultiplexer
from djangochannelsrestframework.mixins import (ListModelMixin, PatchModelMixin, UpdateModelMixin, CreateModelMixin, DeleteModelMixin)
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework import permissions
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.decorators import action


import json

logger = getLogger(__name__)

class MessageConsumer(ListModelMixin, CreateModelMixin, GenericAsyncAPIConsumer):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    chat_room_name : Optional[str]
    chat: Optional[int]

    @action()
    def create(self, data, **kwargs):
        serializer = self.get_serializer(data=data, action_kwargs=kwargs)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer, **kwargs)
        return None, status.HTTP_201_CREATED

    @database_sync_to_async
    def current_user(self) -> ReturnDict:
        return UserSerializer(self.scope["user"], many=False).data

    @action()
    async def join_chat(self, chat: int, **kwargs):
        self.chat_room_name = f"chat_{chat}"
        self.chat = chat
        await self.channel_layer.group_add(
            self.chat_room_name,
            self.channel_name,
        )
        user_serializer = await self.current_user()
        await self.channel_layer.group_send(
            self.chat_room_name,
            {
                "type": "notification",
                "message": f"{self.scope['user'].username} joined the chat",
                "chat": chat,
                "user":user_serializer
            }
        )
    

    async def notification(self, event):
        content = dict(
            action="notification",
            message=event["message"],
            chat=event["chat"],
            user=event["user"],
            status=status.HTTP_200_OK
        )
        await self.send_json(content)

    async def disconnect(self, code):
        if hasattr(self, "chat_room_name"):
            user_serializer = await self.current_user()
            await self.channel_layer.group_send(
                self.chat_room_name,
                {
                    "type": "notification",
                    "message": f"{self.scope['user'].username} leave the chat",
                    "chat": self.chat,
                    "user": user_serializer,
                }
            )
        return await super().disconnect(code)

    @model_observer(Message)
    async def message_create_handler(self, message, observer=None, action=None, **kwargs):
        # due to not being able to make DB QUERIES when selecting a group
        # maybe do an extra check here to be sure the user has permission
        # send activity to your frontend
        await self.send_json(dict(data=message, action=action))

    @message_create_handler.serializer
    def message_create_handler(self, instance: Message, action, **kwargs):
        return MessageSerializer(instance).data

    @message_create_handler.groups_for_signal
    def message_create_handler(self, instance, **kwargs):
        # this block of code is called very often *DO NOT make DB QUERIES HERE*
        yield f'-chat__{instance.chat_id}'

    @message_create_handler.groups_for_consumer
    def message_create_handler(self, chat=None, **kwargs):
        # This is called when you subscribe/unsubscribe
        if chat is not None:
            yield f'-chat__{chat}'

    @action()
    async def subscribe_to_messages_in_chat(self, chat, **kwargs):
        # check user has permission to do this
        if "user" not in self.scope or \
            not self.scope["user"].is_authenticated \
            :
            return {}, status.HTTP_403_FORBIDDEN
        await self.message_create_handler.subscribe(chat=chat)
        return {
            "action": "subscribe_to_messages_in_chat",
            "request_id": kwargs["request_id"],
            "chat": chat,
            "status": status.HTTP_200_OK,
        }, status.HTTP_200_OK


class UserConsumer(ListModelMixin, GenericAsyncAPIConsumer):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ChatConsumer(ListModelMixin, GenericAsyncAPIConsumer):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    @model_observer(Message)
    async def chats_messages_handler(self, message, observer=None, action=None, **kwargs):
        # due to not being able to make DB QUERIES when selecting a group
        # maybe do an extra check here to be sure the user has permission
        # send activity to your frontend
        action = "notification"
        if message["user"]["id"] == self.scope["user"].pk:
            return
        await self.send_json(dict(
            data=message, 
            action=action, 
            response_status=status.HTTP_201_CREATED,
        ))

    @chats_messages_handler.serializer
    def chats_messages_handler(self, instance: Message, action, **kwargs):
        return MessageSerializer(instance).data 

    @chats_messages_handler.groups_for_signal
    def chats_messages_handler(self, instance: Message, **kwargs):
        # this block of code is called very often *DO NOT make DB QUERIES HERE*
        yield f'-chat__{instance.chat_id}'

    @chats_messages_handler.groups_for_consumer
    def chats_messages_handler(self, chat: int, **kwargs):
        # This is called when you subscribe/unsubscribe
        if chat is not None:
            yield f'-chat__{chat}'

    @action()
    async def subscribe_to_notifications(self, **kwargs):
        # check user has permission to do this
        if  "user" not in self.scope or not self.scope["user"].is_authenticated :
            return {}, status.HTTP_403_FORBIDDEN
        queryset = await database_sync_to_async(self.get_queryset)()
        queryset = await database_sync_to_async(queryset.filter)(members=self.scope["user"].pk)
        chats = await database_sync_to_async(list)(queryset)
        # queryset = await database_sync_to_async(self.scope["user"].chats.all)()
        # chats = await database_sync_to_async(list)(queryset)
        for chat in chats:
            await self.chats_messages_handler.subscribe(chat=chat.pk)
        return {}, status.HTTP_201_CREATED


class DemultiplexerAsyncJson(AsyncJsonWebsocketDemultiplexer):
    applications = {
        "user": UserConsumer.as_asgi(),
        "chat": ChatConsumer.as_asgi(),
        "message": MessageConsumer.as_asgi(),
    }
