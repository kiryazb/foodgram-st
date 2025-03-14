from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet, ModelViewSet, ViewSet
from rest_framework.mixins import CreateModelMixin

from .models import CustomUser
from .serializers import UserRegistrationSerializer, UserProfileSerializer, UserListSerializer, AvatarSerializer


class CustomPagination(PageNumberPagination):
    """Кастомная пагинация для списка пользователей"""
    page_size = 10
    page_size_query_param = 'limit'


class UserRegistrationViewSet(CreateModelMixin, GenericViewSet):
    """ViewSet для регистрации пользователей"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        """Создание нового пользователя"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserProfileView(RetrieveAPIView):
    """Получение профиля пользователя по ID"""
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"


class UserListView(ReadOnlyModelViewSet):
    """Получение списка пользователей с пагинацией"""
    queryset = CustomUser.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPagination


class UserViewSet(ModelViewSet):
    """ViewSet для списка пользователей, регистрации и профиля"""
    queryset = CustomUser.objects.all().order_by('id')
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """Используем разные сериализаторы в зависимости от запроса"""
        if self.action in ["list", "retrieve"]:
            return UserListSerializer
        return UserRegistrationSerializer

    @action(detail=False, methods=["get"],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение текущего пользователя (GET /api/users/me/)"""
        serializer = UserListSerializer(
            request.user, context={
                "request": request})
        return Response(serializer.data)


class AvatarView(APIView):
    """Обновление аватара пользователя"""
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = AvatarSerializer(
            user, data=request.data, partial=True, context={
                'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"avatar": user.avatar.url},
                            status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        """Удаление аватара текущего пользователя"""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()
            return Response({"detail": "Аватар успешно удалён."},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Аватар отсутствует."},
                        status=status.HTTP_400_BAD_REQUEST)
