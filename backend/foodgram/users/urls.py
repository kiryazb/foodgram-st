from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileView, UserViewSet, AvatarView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),  # Подключаем ViewSet
    path(
        'users/<int:id>/',
        UserProfileView.as_view(),
        name='user-profile'),
    # Оставляем только user/{id}/
    path('users/me/avatar/', AvatarView.as_view(), name='avatar-update'),
]
