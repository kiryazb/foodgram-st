from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Вьюсеты для User, Recipe и т.д.
from .views import CustomUserViewSet, RecipeViewSet

router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="users")
router.register(r"recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    # Подключаем наши ViewSet-роуты
    path("", include(router.urls)),

    # Подключаем стандартные урлы Djoser (если нужно)
    path("", include("djoser.urls")),
    path("", include("djoser.urls.authtoken")),
]
