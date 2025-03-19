from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from recipes.models import Recipe, User


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "get_author_name")
    search_fields = (
        "name",
        "author__username",
        "author__first_name",
        "author__last_name",
    )
    list_filter = ("author", "name")
    readonly_fields = ("favorites_count",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count("in_favorites"))

    def favorites_count(self, obj):
        return obj.in_favorites.count()

    favorites_count.short_description = "Добавлений в избранное"

    def get_author_name(self, obj):
        return obj.author.username

    get_author_name.short_description = "Автор"


@admin.register(User)
class UserAdmin(UserAdmin):
    """Админка для кастомного пользователя"""

    list_display = ("id", "username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "username")
    ordering = ("id",)
    list_filter = ("is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Персональная информация", {"fields": ("username", "first_name", "last_name", "avatar")}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "first_name", "last_name", "password1", "password2"),
        }),
    )
