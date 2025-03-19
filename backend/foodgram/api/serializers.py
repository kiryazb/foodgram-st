from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.core.files.base import ContentFile
import base64

from rest_framework.pagination import LimitOffsetPagination

from recipes.models import User, Recipe, RecipeIngredient, Subscription, Ingredient, Favorite
from recipes.utils import Base64ImageField


class CustomPagination(LimitOffsetPagination):
    default_limit = 10  # Значение по умолчанию
    max_limit = 100  # Ограничение


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта (используется в избранном)."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписок с поддержкой `recipes_limit`."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        """Проверяем, подписан ли текущий пользователь на данного автора."""
        request = self.context.get("request")
        return (
            request.user.is_authenticated
            and Subscription.objects.filter(user=request.user, author=obj).exists()
        )

    def get_recipes(self, obj):
        """Ограничиваем число рецептов по `recipes_limit`."""
        request = self.context.get("request")
        recipes_limit = self.context.get("recipes_limit")

        queryset = obj.recipes.all()
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                queryset = queryset[:recipes_limit]
            except ValueError:
                pass

        return RecipeShortSerializer(
            queryset, many=True, context={"request": request}
        ).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов у пользователя."""
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


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для записи одного ингредиента в рецепт.
    Проверяем, что id > 0 и что количество amount > 0.
    """

    id = serializers.IntegerField(min_value=1, required=True)
    amount = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения связки "ингредиент в рецепте".
    Достаём id, name, measurement_unit из связанного Ingredient.
    """

    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания/редактирования рецепта.
    Все «служебные» поля (author, is_favorited и т.п.) здесь не нужны:
    - author будет проставлен во вьюхе через perform_create().
    - информация об избранном/корзине отображается только при чтении.
    """

    ingredients = IngredientInRecipeWriteSerializer(many=True, write_only=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "text", "cooking_time", "image", "ingredients")

    def validate_image(self, value):
        """Проверяем, что изображение присутствует"""
        if not value:
            raise serializers.ValidationError(
                "Поле 'image' обязательно для заполнения."
            )
        return value

    def validate_cooking_time(self, value):
        """Убеждаемся, что время приготовления >= 1."""
        if value < 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть не менее 1 минуты."
            )
        return value

    def validate_ingredients(self, ingredients_data):
        """Проверяем, что ингредиенты переданы, существуют и не повторяются."""
        if not ingredients_data:
            raise serializers.ValidationError(
                "Рецепт должен содержать хотя бы один ингредиент."
            )

        ingredient_ids = [item["id"] for item in ingredients_data]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                "Ингредиенты в рецепте не должны повторяться."
            )

        existing_ingredients = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                "id", flat=True
            )
        )
        missing_ingredients = set(ingredient_ids) - existing_ingredients

        if missing_ingredients:
            raise serializers.ValidationError(
                f"Следующие ингредиенты не найдены: {list(missing_ingredients)}"
            )

        return ingredients_data

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)

        # Создаём записи RecipeIngredient
        recipe_ingredients = []
        for item in ingredients_data:
            ingredient = Ingredient.objects.get(id=item["id"])
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient, amount=item["amount"]
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        # Обновляем простые поля рецепта
        ingredients_data = validated_data.pop("ingredients", None)
        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get(
            "cooking_time", instance.cooking_time
        )
        if "image" in validated_data:
            instance.image = validated_data["image"]
        instance.save()

        # Обновляем ингредиенты
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            recipe_ingredients = []
            for item in ingredients_data:
                ingredient = Ingredient.objects.get(id=item["id"])
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=instance, ingredient=ingredient, amount=item["amount"]
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального/листового чтения рецепта.
    Все поля делаем read-only, чтобы случайно не применили
    этот сериализатор к PATCH/POST/PUT-запросам.
    """

    # Автор рецепта (упрощенный вариант). Можно сделать отдельный UserSerializer.
    author = serializers.SerializerMethodField(read_only=True)

    # Список ингредиентов в виде массива {id, name, measurement_unit, amount}
    ingredients = serializers.SerializerMethodField(read_only=True)

    # Показываем только URL изображения (или используем Base64ImageField с read_only=True)
    image = Base64ImageField(read_only=True)

    # Флаги, вычисляемые на лету
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = fields  # Все поля — только для чтения

    def get_author(self, obj):
        user = obj.author
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_subscribed": False,  # пример, реальную логику можно доработать
            "avatar": user.avatar.url if user.avatar else None,
        }

    def get_ingredients(self, obj):
        # Связанные объекты RecipeIngredient
        recipe_ingredients = obj.recipe_ingredients.all()
        return IngredientInRecipeReadSerializer(recipe_ingredients, many=True).data

    def get_is_in_shopping_cart(self, obj):
        """
        Возвращаем True/False, есть ли этот рецепт в корзине у текущего пользователя.
        Используем «ленивую» форму: user.is_authenticated и ...
        """
        user = self.context["request"].user
        return user.is_authenticated and obj.in_shopping_cart.filter(user=user).exists()

    def get_is_favorited(self, obj):
        """
        Возвращаем True/False, есть ли этот рецепт в избранном у текущего пользователя.
        Аналогичная логика.
        """
        user = self.context["request"].user
        return (
            user.is_authenticated
            and Favorite.objects.filter(user=user, recipe=obj).exists()
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
