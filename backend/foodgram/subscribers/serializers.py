from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Subscription
from recipes.models import Recipe  # Импортируем модель рецептов

User = get_user_model()


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для списка рецептов."""

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="author.email", read_only=True)
    id = serializers.IntegerField(source="author.id", read_only=True)
    username = serializers.CharField(source="author.username", read_only=True)
    first_name = serializers.CharField(source="author.first_name", read_only=True)
    last_name = serializers.CharField(source="author.last_name", read_only=True)
    avatar = serializers.ImageField(source="author.avatar", read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="author.recipes.count", read_only=True
    )

    class Meta:
        model = Subscription
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        ]

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        """Ограничиваем количество рецептов через параметр `recipes_limit`."""
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")

        recipes = Recipe.objects.filter(author=obj.author)
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[: int(recipes_limit)]

        return RecipeShortSerializer(recipes, many=True).data


class SubscriptionListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    email = serializers.EmailField(source="author.email", read_only=True)
    id = serializers.IntegerField(source="author.id", read_only=True)
    username = serializers.CharField(source="author.username", read_only=True)
    first_name = serializers.CharField(source="author.first_name", read_only=True)
    last_name = serializers.CharField(source="author.last_name", read_only=True)
    avatar = serializers.ImageField(source="author.avatar", read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="author.recipes.count", read_only=True
    )

    class Meta:
        model = Subscription
        fields = [
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        ]

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        """Ограничиваем количество рецептов через параметр `recipes_limit`."""
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")

        recipes = Recipe.objects.filter(author=obj.author)
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[: int(recipes_limit)]

        return RecipeShortSerializer(recipes, many=True).data
