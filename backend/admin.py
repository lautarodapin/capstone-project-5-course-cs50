from django.contrib import admin       

from .models import User, Chat, Message


@admin.register(User)
class UserAdmin(admin.ModelAdmin):     
    list_display = (
        'id',
        'password',
        'last_login',
        'is_superuser',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = (
        'last_login',
        'is_superuser',
        'is_staff',
        'is_active',
        'date_joined',
    )
    raw_id_fields = ('groups', 'user_permissions')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'mod_at', 'is_group', 'chat_name')
    list_filter = ('created_at', 'mod_at', 'is_group')
    raw_id_fields = ('members',)
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'mod_at', 'user', 'chat', 'text')
    list_filter = ('created_at', 'mod_at', 'user', 'chat')
    date_hierarchy = 'created_at'