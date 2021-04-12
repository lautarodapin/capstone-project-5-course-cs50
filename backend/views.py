from typing import List
from django.db.models import query
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import IntegrityError
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.contrib.auth import authenticate, login, logout
from .models import (User, Chat, Message)
from .serializers import (UserSerializer, ChatSerializer, MessageSerializer)
import json


class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # TODO should only be for creating

    @action(detail=False, methods=["GET"])
    def current_chats(self, request):
        user = request.user
        chats = user.chats.all()
        serializer = ChatSerializer(instance=chats, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"])
    def contacts(self, request):
        user : User = request.user
        users = self.get_queryset().exclude(username=user.username)
        serializer = UserSerializer(instance=users, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class ChatViewset(ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def create_chat_with(self, request):
        queryset = self.get_queryset()
        members: List[int] = request.data.get("members")
        queryset = queryset.filter(members=members[0]) & queryset.filter(members=members[1])
        if queryset.exists(): # If the chat already exist return that.
            serializer : ChatSerializer = ChatSerializer(instance=queryset.first(), many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer : ChatSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        chat : Chat = serializer.instance
        for member in members:
            chat.members.add(member)
        chat.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewset(ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def messages_in_chat(self, request):
        chat_id = request.query_params.get("chat_id")
        queryset = self.get_queryset().filter(chat_id=chat_id)
        page = self.paginate_queryset(queryset)
        serializer = MessageSerializer(instance=page, many=True)
        return self.get_paginated_response(serializer.data)


class CurrentUserView(APIView):
    # authentication_classes = [IsAuthenticated]

    def get(self, request, format=None):
        if request.user.is_authenticated:
            serializer = UserSerializer(instance=request.user)
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect("/")
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect("/")
    else:
        return render(request, "register.html")

