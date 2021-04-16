from logging import getLogger
from typing import Dict, OrderedDict, Union
from django.db.models import query
import pytest
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
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

class MessageConsumer(ListModelMixin, GenericAsyncAPIConsumer):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

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
        yield f'-pk__{instance.pk}'

    @message_create_handler.groups_for_consumer
    def message_create_handler(self, chat=None, **kwargs):
        # This is called when you subscribe/unsubscribe
        if chat is not None:
            yield f'-chat__{chat}'

    @action()
    async def subscribe_to_messages_in_chat(self, chat, **kwargs):
        # check user has permission to do this
        await self.message_create_handler.subscribe(chat=chat)
        await self.send_json({
            "action": "subscribe_to_messages_in_chat",
            "request_id": kwargs["request_id"],
            "chat": chat,
            "status": status.HTTP_200_OK,
        })
    # TODO make test

class UserConsumer(ListModelMixin, GenericAsyncAPIConsumer):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ChatConsumer(ListModelMixin, GenericAsyncAPIConsumer):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer



class DemultiplexerAsyncJson(AsyncJsonWebsocketDemultiplexer):
    applications = {
        "user": UserConsumer.as_asgi(),
        "chat": ChatConsumer.as_asgi(),
        "message": MessageConsumer.as_asgi(),
    }