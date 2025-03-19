from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import Recipe, User, Ingredient, Subscription

from django.utils.safestring import mark_safe


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр по времени приготовления"""
    title = "Время готовки"
    parameter_name = "cooking_time_category"

    def lookups(self, request, model_admin):
        return [
            ("fast", "Быстрое (≤10 мин)"),
            ("medium", "Среднее (11-30 мин)"),
            ("long", "Долгое (>30 мин)"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "fast":
            return queryset.filter(cooking_time__lte=10)
        if self.value() == "medium":
            return queryset.filter(cooking_time__gt=10, cooking_time__lte=30)
        if self.value() == "long":
            return queryset.filter(cooking_time__gt=30)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = (
        "id",
        "name",
        "cooking_time",
        "get_author_name",
        "get_favorites_count",
        "get_ingredients",
        "get_image",
    )

    search_fields = ("name", "author__username", "author__first_name", "author__last_name")
    list_filter = ("author", "name", CookingTimeFilter)

    @admin.display(description="Автор")
    def get_author_name(self, recipe):
        return recipe.author.get_full_name() or recipe.author.username

    @admin.display(description="Добавлений в избранное")
    def get_favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description="Ингредиенты")
    def get_ingredients(self, recipe):
        """Выводит список ингредиентов в админке."""
        ingredients = recipe.ingredients.values_list("ingredient__name", flat=True)
        return ", ".join(ingredients)

    @admin.display(description="Изображение")
    def get_image(self, recipe):
        """Отображает картинку в админке."""
        if recipe.image:
            return mark_safe(f'<img src="{recipe.image.url}" width="75" height="75" />')
        return "Нет изображения"


@admin.register(User)
class UserAdmin(UserAdmin):
    """Админка для кастомного пользователя"""

    list_display = ("id", "username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "username")
    ordering = ("id",)
    list_filter = ("is_staff", "is_superuser", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Персональная информация",
            {"fields": ("username", "first_name", "last_name", "avatar")},
        ),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
    list_filter = ("user", "author")