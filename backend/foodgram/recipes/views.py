from django_filters import FilterSet, NumberFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status

from recipes.models import Recipe
from recipes.serializers import RecipeReadSerializer, RecipeCreateSerializer


class RecipePagination(PageNumberPagination):
    """Пагинация для рецептов."""

    page_size = 10  # Количество объектов на одной странице
    page_size_query_param = "limit"  # Позволяет пользователю указывать `?limit=5`
    max_page_size = 100  # Максимально допустимое количество на странице


class RecipeFilter(FilterSet):
    """Фильтр для поиска рецептов по автору, избранному и корзине."""

    author = NumberFilter(field_name="author__id")
    is_in_shopping_cart = NumberFilter(method="filter_in_shopping_cart")
    is_favorited = NumberFilter(method="filter_is_favorited")

    class Meta:
        model = Recipe
        fields = ["author", "is_in_shopping_cart", "is_favorited"]

    def filter_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты, находящиеся в списке покупок пользователя, если `is_in_shopping_cart=1`."""
        print(f"Фильтрация: is_in_shopping_cart={value}")  # Debug

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            return queryset.filter(in_shopping_cart__user=user)

        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты, находящиеся в избранном пользователя, если `is_favorited=1`."""
        print(f"Фильтрация: is_favorited={value}")

        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        if value == 1:
            return queryset.filter(in_favorites__user=user)

        return queryset


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        # Если list/retrieve → RecipeReadSerializer, иначе →
        # RecipeCreateSerializer
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        # При создании указываем автора
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        # Проверяем, что обновляет автор (опционально)
        recipe = self.get_object()
        if recipe.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Вы не являетесь автором данного рецепта.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        # Проверяем, что удаляет автор
        if recipe.author != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Вы не являетесь автором данного рецепта.")

        # Если всё ок, удаляем
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку для указанного рецепта.
        """
        recipe = self.get_object()  # Получаем рецепт из базы по id (pk)

        # Формируем короткую ссылку (пример - используем ID рецепта)
        short_link = f"https://foodgram.example.org/s/{recipe.id}"

        return Response({"short-link": short_link}, status=status.HTTP_200_OK)
