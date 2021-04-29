from backend.serializers import UserSerializer
from django import dispatch
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import (Message, MessageNotification, User)

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(signal=post_save, sender=User)
def create_token_after_save(sender, instance: User, created: bool, **kwargs):
    if created:
        Token.objects.create(user=instance)

@receiver(signal=post_save, sender=Message)
def send_notification_after_creating_message(sender, instance: Message, created: bool, **kwargs):
    if created:
        chat_id : int = instance.chat.pk
        user_serializer = UserSerializer(instance=instance.user, many=False).data
        room_group_name : str = f"chat_{chat_id}"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "notification",
                "message": instance.text,
                "user": user_serializer,
                "from": instance.user.pk,
                "chat": chat_id,
                "status": status.HTTP_200_OK,
            },
        )



@receiver(signal=post_save, sender=Message)
def create_message_notification(sender, instance: Message, created: bool, **kwargs):
    if created:
        from_user : User = instance.user
        to_user : User = instance.chat.members.exclude(id=from_user.pk).first()
        if to_user != from_user:
            MessageNotification.create_from_message(instance, from_user=from_user, to_user=to_user)