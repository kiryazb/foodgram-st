from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'avatar',
        'is_subscribed_display',
        'is_active',
        'is_staff',
        'date_joined',
        'last_login')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser')

    ordering = ('id',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password', 'avatar')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': (
                'wide',), 'fields': (
                'email', 'username', 'first_name', 'last_name', 'password1', 'password2'), }), )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    @admin.display(description="Подписчиков")
    def is_subscribed_display(self, obj):
        """Возвращает количество подписчиков у пользователя."""
        return obj.followers.count()  # Подсчитываем количество подписчиков
