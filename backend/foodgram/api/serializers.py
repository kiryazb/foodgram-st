from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.core.files.base import ContentFile
import base64

from rest_framework.pagination import LimitOffsetPagination

from recipes.models import User, Recipe


class CustomPagination(LimitOffsetPagination):
    default_limit = 10  # Значение по умолчанию
    max_limit = 100  # Ограничение


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий сериализатор рецептов для подписки."""

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(UserSerializer):
    """Сериализатор пользователя в подписке, добавляет рецепты."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + (
            "is_subscribed",
            "avatar",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        """Определяем, подписан ли текущий пользователь на этого пользователя."""
        request_user = self.context["request"].user
        if not request_user or not request_user.is_authenticated:
            return False
        return obj.followers.filter(user=request_user).exists()

    def get_avatar(self, obj):
        """Возвращаем URL аватара пользователя."""
        return obj.avatar.url if obj.avatar else None

    def get_recipes(self, obj):
        """Возвращаем список рецептов пользователя с ограничением по параметру `recipes_limit`."""
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")

        try:
            recipes_limit = int(recipes_limit) if recipes_limit else None
        except ValueError:
            recipes_limit = None

        recipes = obj.recipes.all()
        if recipes_limit is not None:
            recipes = recipes[:recipes_limit]

        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Возвращаем количество рецептов у пользователя."""
        return obj.recipes.count()


class UserProfileSerializer(UserSerializer):
    """Сериализатор профиля пользователя с дополнительными полями."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ("is_subscribed", "avatar")

    def get_is_subscribed(self, user_obj):
        current_user = self.context["request"].user
        if not current_user.is_authenticated:
            return False
        return user_obj.followers.filter(user=current_user).exists()

    def get_avatar(self, user_obj):
        if user_obj.avatar:
            return user_obj.avatar.url
        return None


class AvatarSerializer(serializers.ModelSerializer):
    avatar = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["avatar"]

    def validate_avatar(self, base64_string):
        """Декодируем base64 и создаём файл-объект."""
        if "avatar" not in self.initial_data:
            raise serializers.ValidationError("Поле 'avatar' отсутствует в запросе.")

        if not base64_string:
            raise serializers.ValidationError("Поле 'avatar' обязательно.")

        try:
            format, img_str = base64_string.split(";base64,")
            ext = format.split("/")[-1]
            decoded_img = base64.b64decode(img_str)
        except Exception:
            raise serializers.ValidationError("Некорректный формат изображения.")

        return ContentFile(decoded_img, name=f"user_avatar.{ext}")

    def update(self, instance, validated_data):
        if "avatar" not in validated_data:
            raise serializers.ValidationError({"avatar": "Поле 'avatar' обязательно."})
        instance.avatar = validated_data["avatar"]
        instance.save()
        return instance
