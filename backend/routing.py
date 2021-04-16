from django.urls import path
from django.urls.conf import re_path
from . import consumers

websocket_url_patterns = [
    re_path(r"^ws/$", consumers.DemultiplexerAsyncJson.as_asgi()),
    path("ws/chat/<int:chat_id>/", consumers.ChatConsumer.as_asgi()),
]