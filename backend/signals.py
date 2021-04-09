from django import dispatch
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import (User)

@receiver(signal=post_save, sender=User)
def create_token_after_save(sender, instance: User, created, **kwargs):
    if not instance.auth_token.exists():
        Token.objects.create(user=instance)