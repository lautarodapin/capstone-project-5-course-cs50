from typing import Tuple
from django.utils import translation
import pytest
import backend.signals
from backend.models import Chat, Message, MessageNotification, User

@pytest.fixture
def basic_users()->Tuple[User, User, Chat]:
    user1 : User = User.objects.create_user(username="test1", password="testpassword123")
    user2 : User = User.objects.create_user(username="test2", password="testpassword123")
    chat : Chat = Chat.objects.create()
    chat.members.add(user1.pk)
    chat.members.add(user2.pk)
    chat.save()
    return user1, user2, chat


@pytest.mark.django_db(transaction=True)
def test_signal_create_token_after_save():
    test : User = User.objects.create_user(username="test_user", password="testpassword123")
    assert test.auth_token is not None

@pytest.mark.django_db(transaction=True)
def test_create_message_notification_from_message(basic_users):
    user_1, user_2, chat = basic_users
    message : Message = Message.objects.create(
        user=user_1,
        chat=chat,
        text="user 1 sends a message to user 2"
    )
    notification : MessageNotification = message.message_notification
    assert notification
    assert notification.from_user == user_1
    assert notification.user == user_2
    assert notification.is_read == False
    assert notification.message == message
    assert notification.text == message.text
    assert notification.read_time == None