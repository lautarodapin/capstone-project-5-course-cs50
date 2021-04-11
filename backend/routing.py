from django.urls import path
from . import consumers

websocket_url_patterns = [
    path("ws/chat/<int:chat_id>/", consumers.ChatConsumer.as_asgi()),
]