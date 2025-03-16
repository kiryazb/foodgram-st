from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from .models import Subscription
from .serializers import SubscriptionSerializer, SubscriptionListSerializer
from recipes.models import Recipe  # Импортируем рецепты

User = get_user_model()


class SubscriptionPagination(PageNumberPagination):
    """Настройка пагинации для списка подписок."""

    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 100


class SubscriptionListViewSet(ReadOnlyModelViewSet):
    """Возвращает список подписок текущего пользователя с пагинацией."""

    serializer_class = SubscriptionListSerializer
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
