from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import User, Subscription
from subscribers.views import SubscriptionPagination
from .serializers import (
    UserProfileSerializer,
    AvatarSerializer,
    CustomPagination,
    SubscriptionSerializer,
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
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        user = request.user
        subscriptions = User.objects.filter(followers__user=user)

        paginator = SubscriptionPagination()
        paginated_subscriptions = paginator.paginate_queryset(subscriptions, request)

        serializer = SubscriptionSerializer(
            paginated_subscriptions, many=True, context={"request": request}
        )

        return paginator.get_paginated_response(serializer.data)

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

            serializer = SubscriptionSerializer(author, context={"request": request})
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
