from rest_framework.viewsets import ModelViewSet
from .models import (User, Chat, Message)
from .serializers import (UserSerializer, ChatSerializer, MessageSerializer)

class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ChatViewset(ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

class MessageViewset(ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer