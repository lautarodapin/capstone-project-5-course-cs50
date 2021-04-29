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
        ordering = ["created_at"]

    members = models.ManyToManyField(User, related_name="chats")
    is_group = models.BooleanField(default=False)
    chat_name = models.CharField(max_length=255, null=True, blank=True)


class Message(MixinDate):
    class Meta:
        abstract = False
        ordering = ["created_at"]

    user = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, related_name="messages", on_delete=models.CASCADE, db_index=True)
    text = models.TextField()


class MessageNotification(MixinDate):
    class Meta:
        abstract = False
        ordering = ["created_at"]

    from_user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="message_notifications", on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, related_name="message_notifications", on_delete=models.CASCADE, db_index=True)
    message = models.OneToOneField(Message, related_name="message_notification", on_delete=models.CASCADE)
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    read_time = models.DateTimeField(null=True, blank=True)

    @classmethod
    def create_from_message(cls, message: Message, from_user: User, to_user: User):
        return cls.objects.create(
            from_user=from_user,
            user=to_user,
            chat=message.chat,
            message=message,
            text=message.text,
        )