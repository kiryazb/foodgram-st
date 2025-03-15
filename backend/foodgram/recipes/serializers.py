from collections import OrderedDict

from rest_framework import serializers
from .models import Recipe, RecipeIngredient, Ingredient
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
    # Поле для записи ингредиентов
    ingredients = IngredientInRecipeWriteSerializer(many=True, write_only=True)
    # Поле для чтения ингредиентов
    ingredients_read = serializers.SerializerMethodField(read_only=True)

    image = Base64ImageField()

    author = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "author", "ingredients", "ingredients_read", "image", "name", "text", "cooking_time")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['is_favorited'] = True
        data['is_in_shopping_cart'] = True
        print("🔥 to_representation вызван!")  # Проверяем, вызывается ли метод
        return data

    def validate_ingredients(self, ingredients):
        """Проверяем, что список ингредиентов не пуст, не содержит дубликатов и все ингредиенты существуют."""
        if not ingredients:
            raise serializers.ValidationError("Рецепт должен содержать хотя бы один ингредиент.")

        ingredient_ids = [ingredient["id"] for ingredient in ingredients]

        # Проверяем дубликаты
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("В рецепте не должно быть повторяющихся ингредиентов.")

        existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids).values_list("id", flat=True)
        missing_ingredients = set(ingredient_ids) - set(existing_ingredients)
        if missing_ingredients:
            raise serializers.ValidationError(f"Некоторые ингредиенты не существуют: {missing_ingredients}")

        return ingredients

    def validate_cooking_time(self, value):
        """Проверяем, что время приготовления не меньше 1 минуты."""
        if value < 1:
            raise serializers.ValidationError("Время приготовления должно быть минимум 1 минута.")
        return value

    def get_author(self, obj):
        """Формируем структуру данных об авторе."""
        user = obj.author
        return {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_subscribed": False,  # Подписи по желанию
            "avatar": user.avatar.url if user.avatar else None
        }

    def get_ingredients_read(self, obj):
        # obj -- это Recipe
        recipe_ingredients = obj.recipe_ingredients.all()  # Получаем RecipeIngredient
        return IngredientInRecipeReadSerializer(recipe_ingredients, many=True).data

    def create(self, validated_data):
        """Создание нового рецепта."""
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)

        # Создаем RecipeIngredient
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_obj = Ingredient.objects.get(id=ingredient_data["id"])
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient_obj,
                    amount=ingredient_data["amount"]
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта (PATCH/PUT)."""
        # 1. Извлекаем список ингредиентов (если передан)
        ingredients_data = validated_data.pop("ingredients", None)

        if "ingredients" in validated_data and not validated_data["ingredients"]:
            raise serializers.ValidationError({"ingredients": "Рецепт должен содержать хотя бы один ингредиент."})

        if ingredients_data is not None:
            ingredient_ids = [ingredient["id"] for ingredient in ingredients_data]
            existing_ingredients = Ingredient.objects.filter(id__in=ingredient_ids).values_list("id", flat=True)

            missing_ingredients = set(ingredient_ids) - set(existing_ingredients)
            if missing_ingredients:
                raise serializers.ValidationError(
                    {"ingredients": f"Некоторые ингредиенты не существуют: {missing_ingredients}"})

            if len(ingredient_ids) != len(set(ingredient_ids)):
                raise serializers.ValidationError(
                    {"ingredients": "В рецепте не должно быть повторяющихся ингредиентов."})

            if "cooking_time" in validated_data and validated_data["cooking_time"] < 1:
                raise serializers.ValidationError({"cooking_time": "Время приготовления должно быть минимум 1 минута."})

        # 2. Обновляем поля рецепта (name, text, image, cooking_time, и т.д.)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 3. Если в запросе пришли ингредиенты, удаляем старые и создаем новые
        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            new_ri = []
            for ingredient_data in ingredients_data:
                ingredient_obj = Ingredient.objects.get(id=ingredient_data["id"])
                new_ri.append(
                    RecipeIngredient(
                        recipe=instance,
                        ingredient=ingredient_obj,
                        amount=ingredient_data["amount"]
                    )
                )
            RecipeIngredient.objects.bulk_create(new_ri)

        return instance

    def to_representation(self, instance):
        """Вызывается при чтении (GET)."""
        # Сериализуем всю модель Recipe стандартно
        ret = super().to_representation(instance)

        # Заменим поле 'ingredients' в выводе на 'ingredients_read'
        ret["ingredients"] = ret.pop("ingredients_read")
        return ret


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
            "id", "author", "ingredients",
            "is_favorited", "is_in_shopping_cart",
            "name", "image", "text", "cooking_time"
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
        # Получаем все RecipeIngredient для этого рецепта
        recipe_ingredients = obj.recipe_ingredients.all()
        return IngredientInRecipeReadSerializer(recipe_ingredients, many=True).data

    def get_is_favorited(self, obj):
        return True

    def get_is_in_shopping_cart(self, obj):
        return True




