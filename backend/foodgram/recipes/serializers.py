from rest_framework import serializers

from favorites.models import Favorite
from ingredients.models import Ingredient
from .models import Recipe, RecipeIngredient
from .utils import Base64ImageField


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
    image = Base64ImageField()
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

    def validate_ingredients(self, ingredients):
        """Проверяет список ингредиентов."""
        if not ingredients:
            raise serializers.ValidationError("Рецепт должен содержать хотя бы один ингредиент.")

        ingredient_ids = [item["id"] for item in ingredients]

        # Проверка на повторяющиеся ингредиенты
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться.")

        # Проверка существования ингредиентов в БД
        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids).values_list("id", flat=True)
        missing_ingredients = set(ingredient_ids) - set(existing_ingredients)

        if missing_ingredients:
            raise serializers.ValidationError(f"Следующие ингредиенты не найдены: {list(missing_ingredients)}")

        return ingredients

    def validate_cooking_time(self, value):
        """Проверяет, что время приготовления больше или равно 1."""
        if value < 1:
            raise serializers.ValidationError("Время приготовления должно быть не менее 1 минуты.")
        return value

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

    def create(self, validated_data):
        """Создание рецепта с ингредиентами."""
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)

        # Добавляем ингредиенты в рецепт
        ingredient_objects = [
            RecipeIngredient(recipe=recipe, ingredient=Ingredient.objects.get(id=ingredient["id"]), amount=ingredient["amount"])
            for ingredient in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredient_objects)

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами."""
        ingredients_data = validated_data.pop("ingredients", None)

        if ingredients_data is None:
            raise serializers.ValidationError("Ингредиенты не указаны")

        instance.name = validated_data.get("name", instance.name)
        instance.text = validated_data.get("text", instance.text)
        instance.cooking_time = validated_data.get("cooking_time", instance.cooking_time)
        instance.image = validated_data.get("image", instance.image)
        instance.save()

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            ingredient_objects = [
                RecipeIngredient(recipe=instance, ingredient=Ingredient.objects.get(id=ingredient["id"]), amount=ingredient["amount"])
                for ingredient in ingredients_data
            ]
            RecipeIngredient.objects.bulk_create(ingredient_objects)

        return instance


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения детальной информации о рецепте."""

    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField()
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
