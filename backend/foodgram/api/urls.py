from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CustomUserViewSet, RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="users")
router.register(r"recipes", RecipeViewSet, basename="recipes")
router.register(r"ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = [
    # Подключаем наши ViewSet-роуты
    path("", include(router.urls)),

    # Подключаем стандартные урлы Djoser (если нужно)
    path("", include("djoser.urls")),
    path("", include("djoser.urls.authtoken")),
]
