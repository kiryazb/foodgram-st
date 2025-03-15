# favorites/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from favorites.models import Favorite
from favorites.serializers import FavoriteRecipeSerializer
from recipes.models import Recipe


class FavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        """
        Добавляет рецепт (recipe_id) в избранное для текущего пользователя (POST /recipes/<id>/favorite/).
        """
        user = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)

        # Проверяем, не в избранном ли уже рецепт
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite_obj = Favorite.objects.create(user=user, recipe=recipe)
        serializer = FavoriteRecipeSerializer(favorite_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        """
        Удаляет рецепт (recipe_id) из избранного текущего пользователя (DELETE /recipes/<id>/favorite/).
        """
        user = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        favorite_obj = Favorite.objects.filter(user=user, recipe=recipe).first()

        if not favorite_obj:
            return Response(
                {'errors': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )

        favorite_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
