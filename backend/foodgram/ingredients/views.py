from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ingredient
from .serializers import IngredientSerializer

class IngredientViewSet(ReadOnlyModelViewSet):
    """API для получения списка ингредиентов с фильтрацией по имени."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    search_fields = ["^name"]  # Фильтр по вхождению в начало слова
