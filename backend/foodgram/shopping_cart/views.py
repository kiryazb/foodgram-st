from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse

from recipes.models import Recipe, RecipeIngredient
from shopping_cart.models import ShoppingCart
from shopping_cart.serializator import ShoppingCartSerializer
from django.db.models import Sum


class ShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Скачивает список покупок текущего пользователя (текстовый файл).
        Предполагается, что URL для вызова этого метода —
        """
        user = request.user

        # Получаем все записи из корзины текущего пользователя
        cart_items = ShoppingCart.objects.filter(user=user).select_related('recipe')

        # Собираем ID всех рецептов в корзине
        recipe_ids = cart_items.values_list('recipe__id', flat=True)

        # Из таблицы RecipeIngredient берём ингредиенты для этих рецептов
        ingredients_qs = RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)

        # Группируем и суммируем количество по имени и ед. измерения ингредиента
        ingredients_data = (
            ingredients_qs
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

        # Формируем текст для выдачи
        lines = []
        for item in ingredients_data:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            amount = item['total_amount']
            lines.append(f'{name} ({unit}) — {amount}')

        content = '\n'.join(lines)

        # Возвращаем файл с заголовком на скачивание
        response = HttpResponse(content, content_type='text/plain; charset=UTF-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    def post(self, request, recipe_id):
        user = request.user
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Рецепт не найден.'},
                            status=status.HTTP_404_NOT_FOUND)

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            return Response({'error': 'Рецепт уже в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        shopping_cart = ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = ShoppingCartSerializer(shopping_cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        """Удаляет рецепт из списка покупок."""
        user = request.user
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({'error': 'Рецепт не найден.'},
                            status=status.HTTP_404_NOT_FOUND)

        cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe).first()
        if not cart_item:
            return Response({'error': 'Рецепта нет в списке покупок.'},
                            status=status.HTTP_400_BAD_REQUEST)

        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
