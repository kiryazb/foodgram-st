from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import (
    Recipe,
    User,
    Ingredient,
    Subscription,
    ShoppingCart,
    Favorite,
)

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

    search_fields = (
        "name",
        "author__username",
        "author__first_name",
        "author__last_name",
    )
    list_filter = ("author", "name", CookingTimeFilter)

    @admin.display(description="Автор")
    def get_author_name(self, recipe):
        return recipe.author.get_full_name() or recipe.author.username

    @admin.display(description="В избранное")
    def get_favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description="Ингредиенты")
    def get_ingredients(self, recipe):
        """Выводит список ингредиентов в админке с количеством и единицей измерения."""
        return mark_safe(
            "<br>".join(
                f"{ingredient.ingredient.name} - {ingredient.amount} {ingredient.ingredient.measurement_unit}"
                for ingredient in recipe.recipe_ingredients.all()
            )
        )

    @admin.display(description="Изображение")
    def get_image(self, recipe):
        """Отображает картинку в админке."""
        if recipe.image:
            return mark_safe(f'<img src="{recipe.image.url}" width="75" height="75" />')
        return "Нет изображения"


@admin.register(User)
class UserAdmin(UserAdmin):
    """Админка для кастомного пользователя"""

    list_display = (
        "id",
        "username",
        "email",
        "get_full_name",
        "get_avatar",
        "get_recipe_count",
        "get_followers_count",
        "get_following_count",
    )
    search_fields = ("email", "username", "first_name", "last_name")
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

    @admin.display(description="ФИО")
    def get_full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    @admin.display(description="Аватар")
    @mark_safe
    def get_avatar(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="50" height="50" style="border-radius: 50%;" />'
        return "Нет аватара"

    @admin.display(description="Рецептов")
    def get_recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description="Подписчиков")
    def get_followers_count(self, user):
        return user.followers.count()

    @admin.display(description="Подписок")
    def get_following_count(self, user):
        return user.following.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ("id", "name", "measurement_unit", "get_recipe_count")
    search_fields = ("name", "measurement_unit")
    list_filter = ("measurement_unit",)
    ordering = ("name",)

    @admin.display(description="Используется в рецептах")
    def get_recipe_count(self, ingredient):
        """Подсчитывает количество рецептов, где используется ингредиент."""
        return ingredient.recipeingredient_set.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
    list_filter = ("user", "author")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("user", "recipe")
