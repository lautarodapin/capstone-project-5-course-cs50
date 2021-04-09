from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields import related

class MixinDate(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(auto_now_add=True)
    mod_at = models.DateTimeField(auto_now=True)


class User(AbstractUser):
    pass


class Chat(MixinDate):
    class Meta:
        abstract = False
        ordering = ["-created_at"]

    members = models.ManyToManyField(User, related_name="chats")
    is_group = models.BooleanField(default=False)
    chat_name = models.CharField(max_length=255, null=True, blank=True)


class Message(MixinDate):
    class Meta:
        abstract = False
        ordering = ["-created_at"]

    user = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, related_name="messages", on_delete=models.CASCADE, db_index=True)
    text = models.TextField()