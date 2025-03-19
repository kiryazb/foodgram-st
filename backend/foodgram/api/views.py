from datetime import datetime
from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters import FilterSet, NumberFilter, CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (
    User,
    Subscription,
    Recipe,
    Ingredient,
    ShoppingCart,
    Favorite,
    RecipeIngredient,
)
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    UserProfileSerializer,
    AvatarSerializer,
    Pagination,
    UserSubscriptionSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeShortSerializer,
    IngredientSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """
    Наследуемся от стандартного djoser.views.UserViewSet,
    чтобы переопределить/добавить нужные методы.
    """

    pagination_class = Pagination
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
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"avatar": user.avatar.url}, status=200)

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

        serializer = UserSubscriptionSerializer(
            paginated_subscriptions,
            many=True,
            context={"request": request},
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

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )

            if not created:
                return Response(
                    {"error": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            recipes_limit = request.query_params.get("recipes_limit")

            serializer = UserSubscriptionSerializer(
                author, context={"request": request, "recipes_limit": recipes_limit}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(Subscription, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        elif self.action == "create":
            return [IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthorOrReadOnly()]
        return super().get_permissions()

    def get_serializer_class(self):
        """
        Для списка / детального просмотра → RecipeReadSerializer,
        для создания / обновления → RecipeWriteSerializer
        """
        if self.action in ["list", "retrieve"]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """Сохранение рецепта с автором."""
        serializer.save(author=self.request.user)

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
        recipe = Recipe.objects.filter(pk=pk).first()

        if recipe and request.method == "POST":
            obj, created = model.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response(
                    {"error": error_message.format(recipe.name)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeShortSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(model, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в корзину покупок."""
        return self.toggle_relation(
            request,
            pk,
            ShoppingCart,
            error_message='Рецепт "{}" уже в корзине.',
            success_message='Рецепт "{}" отсутствует в корзине.',
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        url_path="favorite",
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавление/удаление рецепта в избранное."""
        return self.toggle_relation(
            request,
            pk,
            Favorite,
            error_message='Рецепт "{}" уже в избранном.',
            success_message='Рецепт "{}" не найден в избранном.',
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[IsAuthenticated],
    )
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

        recipes = (
            Recipe.objects.filter(id__in=recipe_ids)
            .select_related("author")
            .values(
                "name", "author__first_name", "author__last_name", "author__username"
            )
        )

        date_str = datetime.now().strftime("%d.%m.%Y %H:%M")

        header = f"Список покупок (составлен: {date_str})\n"
        product_header = "№ | Продукт | Количество | Ед. изм.\n"
        recipe_header = "\nИспользуется в рецептах:\n"

        products = [
            f"{idx + 1} | {item['ingredient__name'].capitalize()} | {item['total_amount']} | {item['ingredient__measurement_unit']}"
            for idx, item in enumerate(ingredients_data)
        ]

        recipe_list = [
            f"- {recipe['name']} (Автор: {recipe['author__first_name']} {recipe['author__last_name'] or recipe['author__username']})"
            for recipe in recipes
        ]

        content = "\n".join(
            [header, product_header, *products, recipe_header, *recipe_list]
        )

        # Используем BytesIO для создания файла в памяти
        buffer = BytesIO()
        buffer.write(content.encode("utf-8"))
        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename="shopping_list.txt",
            content_type="text/plain",
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """
        Возвращает короткую ссылку на рецепт.
        """
        recipe = self.get_object()
        relative_url = f"/s/{recipe.id}"
        short_link = request.build_absolute_uri(relative_url)
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
