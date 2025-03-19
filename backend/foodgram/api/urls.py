from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet

router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="users")

urlpatterns = [
    # Роутер для кастомного UserViewSet
    path("", include(router.urls)),

    # Подключаем стандартные урлы Djoser
    path("", include("djoser.urls")),
    path("", include("djoser.urls.authtoken")),

    # Можно добавить прочие include(...), если у вас есть другие эндпоинты
]
