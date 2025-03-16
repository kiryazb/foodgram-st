from rest_framework import serializers

from favorites.models import Favorite
from .models import Recipe, RecipeIngredient


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиента."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения RecipeIngredient."""

    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(source="ingredient.measurement_unit")
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeWriteSerializer(many=True, write_only=True)
    ingredients_read = serializers.SerializerMethodField(read_only=True)
    image = serializers.SerializerMethodField()  # Делаем кастомное поле
    author = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "ingredients_read",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["ingredients"] = ret.pop("ingredients_read")
        return ret

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.in_shopping_cart.filter(user=user).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_author(self, obj):
        user = obj.author
        return {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_subscribed": False,
            "avatar": user.avatar.url if user.avatar else None,
        }

    def get_ingredients_read(self, obj):
        recipe_ingredients = obj.recipe_ingredients.all()
        return IngredientInRecipeReadSerializer(recipe_ingredients, many=True).data

    def get_image(self, obj):
        """Возвращает относительный путь к изображению"""
        if obj.image:
            return obj.image.url  # Вернёт "/media/recipes/image.png"
        return None


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения детальной информации о рецепте."""

    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()  # Используем кастомное поле
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_author(self, obj):
        user = obj.author
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_subscribed": False,
            "avatar": user.avatar.url if user.avatar else None,
        }

    def get_ingredients(self, obj):
        recipe_ingredients = obj.recipe_ingredients.all()
        return IngredientInRecipeReadSerializer(recipe_ingredients, many=True).data

    def get_is_favorited(self, obj):
        return True

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.in_shopping_cart.filter(user=user).exists()
        return False

    def get_image(self, obj):
        """Возвращает относительный путь к изображению"""
        if obj.image:
            return obj.image.url  # Вернёт "/media/recipes/image.png"
        return None
