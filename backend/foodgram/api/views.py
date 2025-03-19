from django.db.models import Sum
from django.http import HttpResponse
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
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from recipes.models import User, Subscription, Recipe, Ingredient, ShoppingCart, Favorite, RecipeIngredient
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
        response_serializer = RecipeReadSerializer(recipe, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def toggle_relation(self, request, pk, model, error_message, success_message):
        """
        Универсальный метод для добавления/удаления рецептов из Избранного и Корзины.

        Аргументы:
        - request: объект запроса
        - pk: ID рецепта
        - model: модель, в которой нужно создать или удалить запись (Favorite или ShoppingCart)
        - error_message: сообщение при попытке повторного добавления
        - success_message: сообщение при успешном удалении
        """
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            obj, created = model.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response(
                    {"error": error_message.format(recipe.name)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeShortSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
            if not deleted:
                return Response(
                    {"error": success_message.format(recipe.name)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в корзину покупок."""
        return self.toggle_relation(
            request, pk, ShoppingCart,
            error_message='Рецепт "{}" уже в корзине.',
            success_message='Рецепт "{}" отсутствует в корзине.'
        )

    @action(detail=True, methods=["post", "delete"], url_path="favorite", permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        return self.toggle_relation(
            request, pk, Favorite,
            error_message='Рецепт "{}" уже в избранном.',
            success_message='Рецепт "{}" не найден в избранном.'
        )

    @action(detail=False, methods=["get"], url_path="download_shopping_cart", permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Формирует и скачивает список покупок в формате .txt.
        """
        user = request.user
        cart_items = ShoppingCart.objects.filter(user=user).select_related("recipe")

        if not cart_items.exists():
            return Response({"error": "Ваша корзина пуста."}, status=400)

        recipe_ids = cart_items.values_list("recipe__id", flat=True)

        ingredients_qs = RecipeIngredient.objects.filter(recipe_id__in=recipe_ids)

        ingredients_data = (
            ingredients_qs.values("ingredient__name", "ingredient__measurement_unit")
            .annotate(total_amount=Sum("amount"))
            .order_by("ingredient__name")
        )

        # Готовим содержимое файла
        lines = ["Список покупок:\n"]
        for item in ingredients_data:
            name = item["ingredient__name"]
            unit = item["ingredient__measurement_unit"]
            amount = item["total_amount"]
            lines.append(f"{name} ({unit}) — {amount}")

        content = "\n".join(lines)

        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'

        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
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


class SubscriptionPagination(PageNumberPagination):
    """Настройка пагинации для списка подписок."""

    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100


class SubscriptionListViewSet(ReadOnlyModelViewSet):
    """Возвращает список подписок текущего пользователя с пагинацией."""

    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SubscriptionViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request, id=None):
        """Создание подписки на пользователя."""
        author = get_object_or_404(User, id=id)
        user = request.user

        if user == author:
            return Response(
                {"error": "Нельзя подписаться на себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {"error": "Вы уже подписаны"}, status=status.HTTP_400_BAD_REQUEST
            )

        subscription = Subscription.objects.create(user=user, author=author)
        serializer = SubscriptionSerializer(
            subscription, context={"request": request}
        )  # <-- добавили context
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, id=None):
        """Удаление подписки."""
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(user=request.user, author=author)

        if not subscription.exists():
            return Response(
                {"error": "Вы не подписаны"}, status=status.HTTP_400_BAD_REQUEST
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, id=None):
        """Получение информации о подписке (с поддержкой `recipes_limit`)."""
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        ).first()

        if not subscription:
            return Response(
                {"error": "Вы не подписаны"}, status=status.HTTP_404_NOT_FOUND
            )

        recipes_limit = request.query_params.get("recipes_limit")
        recipes = Recipe.objects.filter(author=author)

        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[: int(recipes_limit)]

        serializer = SubscriptionSerializer(subscription, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
