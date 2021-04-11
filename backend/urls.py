from collections import defaultdict
from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    UserViewset, MessageViewset, ChatViewset, 
    CurrentUserView,
    )

router = DefaultRouter()
router.register("users", UserViewset, basename="user")
router.register("messages", MessageViewset, basename="message")
router.register("chats", ChatViewset, basename="chat")

urlpatterns = router.urls + [
    path("current-user/", CurrentUserView.as_view()),
]
