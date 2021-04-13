from django import dispatch
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import (Message, User)

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
        room_group_name : str = f"chat_{chat_id}"
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                "type": "notification",
                "message": instance.text,
                "from": instance.user.pk,
                "chat": instance.chat.pk,
            },
        )
