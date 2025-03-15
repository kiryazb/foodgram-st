# favorites/serializers.py

from rest_framework import serializers
from favorites.models import Favorite
from recipes.models import Recipe


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта внутри избранного."""
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')
