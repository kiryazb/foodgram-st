from django.shortcuts import get_object_or_404
from django_filters import FilterSet, NumberFilter, CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from favorites.models import Favorite
from recipes.models import User, Subscription, Recipe, Ingredient
from shopping_cart.models import ShoppingCart
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    UserProfileSerializer,
    AvatarSerializer,
    CustomPagination,
    SubscriptionSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    IngredientSerializer,
)


class CustomUserViewSet(DjoserUserViewSet):
    """
    Наследуемся от стандартного djoser.views.UserViewSet,
    чтобы переопределить/добавить нужные методы.
    """

    pagination_class = CustomPagination
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        """Переопределяем разрешения для разных эндпоинтов."""
        if self.action in ["me", "avatar"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        methods=["put", "delete"],
        detail=False,
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request, *args, **kwargs):
        """
        Метод для обновления (PUT) или удаления (DELETE) аватара
        текущего пользователя по эндпоинту /users/me/avatar/.
        """
        user = request.user

        if request.method == "PUT":
            serializer = AvatarSerializer(
                user, data=request.data, partial=True, context={"request": request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response({"avatar": user.avatar.url}, status=200)
            return Response(serializer.errors, status=400)

        elif request.method == "DELETE":
            if user.avatar:
                user.avatar.delete()
                user.save()
                return Response({"detail": "Аватар успешно удалён."}, status=204)
            return Response({"detail": "Аватар отсутствует."}, status=400)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя с поддержкой пагинации."""
        user = request.user
        subscriptions = User.objects.filter(followers__user=user)

        paginator = self.paginator
        paginated_subscriptions = paginator.paginate_queryset(subscriptions, request)

        # Извлекаем параметр `recipes_limit` из запроса
        recipes_limit = request.query_params.get("recipes_limit")

        serializer = SubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context={"request": request, "recipes_limit": recipes_limit},
        )

        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        """Подписка и отписка на пользователя."""
        user = request.user
        author = self.get_object()

        if request.method == "POST":
            if user == author:
                return Response(
                    {"error": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"error": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Subscription.objects.create(user=user, author=author)

            recipes_limit = request.query_params.get("recipes_limit")

            serializer = SubscriptionSerializer(
                author, context={"request": request, "recipes_limit": recipes_limit}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            subscription = Subscription.objects.filter(user=user, author=author)
            if not subscription.exists():
                return Response(
                    {"error": "Вы не подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription.delete()
            return Response(
                {"detail": "Подписка удалена."}, status=status.HTTP_204_NO_CONTENT
            )


class RecipePagination(PageNumberPagination):
    """Пагинация для рецептов."""

    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100


class RecipeFilter(FilterSet):
    """
    Фильтр для поиска рецептов по автору, избранному и корзине.
    Переименовываем 'queryset' → 'recipes_qs'.
    """

    author = NumberFilter(field_name="author_id")
    is_in_shopping_cart = NumberFilter(method="filter_in_shopping_cart")
    is_favorited = NumberFilter(method="filter_is_favorited")

    class Meta:
        model = Recipe
        fields = ["author", "is_in_shopping_cart", "is_favorited"]

    def filter_in_shopping_cart(self, recipes_qs, name, value):
        """
        Фильтрует рецепты, находящиеся в корзине текущего пользователя, если is_in_shopping_cart=1
        """
        user = self.request.user
        if not user.is_authenticated:
            return recipes_qs.none() if value == 1 else recipes_qs

        if value == 1:
            return recipes_qs.filter(in_shopping_cart__user=user)
        return recipes_qs

    def filter_is_favorited(self, recipes_qs, name, value):
        """
        Фильтрует рецепты, находящиеся в избранном пользователя, если is_favorited=1
        """
        user = self.request.user
        if not user.is_authenticated:
            return recipes_qs.none() if value == 1 else recipes_qs

        if value == 1:
            return recipes_qs.filter(in_favorites__user=user)
        return recipes_qs


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = RecipePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        """
        Для списка / детального просмотра → RecipeReadSerializer,
        для создания / обновления → RecipeWriteSerializer
        """
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        """
        Переопределяем create, чтобы вернуть ответ в формате RecipeReadSerializer.
        """
        if not request.user or request.user.is_anonymous:
            raise NotAuthenticated("Вы должны быть авторизованы для создания рецепта.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)

        # Возвращаем данные в формате RecipeReadSerializer
        response_serializer = RecipeReadSerializer(recipe, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Переопределяем update, чтобы вернуть ответ в формате RecipeReadSerializer.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        if partial and "ingredients" not in request.data:
            return Response(
                {"error": "Поле 'ingredients' обязательно при обновлении рецепта."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        # Возвращаем данные в формате RecipeReadSerializer
        response_serializer = RecipeReadSerializer(recipe, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """
        Добавить/удалить рецепт из избранного.
        """
        recipe = self.get_object()

        if request.method == "POST":
            favorite, created = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                serializer = RecipeShortSerializer(recipe, context={"request": request})
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )  # Теперь 201 и JSON-ответ
            return Response(
                {"error": "Рецепт уже в избранном."}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == "DELETE":
            deleted, _ = Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            if deleted:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"error": "Рецепт не найден в избранном."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="shopping_cart",
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавить/удалить рецепт в корзину покупок.
        """
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"error": "Рецепт уже в корзине."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            shopping_cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not shopping_cart_item.exists():
                return Response(
                    {"error": "Рецепт отсутствует в корзине."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            shopping_cart_item.delete()
            return Response(
                {"detail": "Рецепт удалён из корзины."},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        """
        Выгрузить список покупок (не привязан к конкретному pk).
        detail=False -> эндпоинт /recipes/download_shopping_cart/
        """
        # Логика выгрузки
        # ...
        return Response({"status": "ok"})

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку для рецепта.
        """
        recipe = self.get_object()
        short_link = f"https://localhost/s/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class IngredientFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="istartswith")  # Начало слова

    class Meta:
        model = Ingredient
        fields = ["name"]


class IngredientViewSet(ReadOnlyModelViewSet):
    """API для получения списка ингредиентов с фильтрацией по началу имени."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter  # Используем кастомный фильтр
    pagination_class = None
