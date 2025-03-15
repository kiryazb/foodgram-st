from django.urls import path, include
from rest_framework.routers import DefaultRouter

from favorites.views import FavoriteView
from shopping_cart.views import ShoppingCartView
from .views import RecipeViewSet

router = DefaultRouter()
router.register(r"recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path('recipes/download_shopping_cart/', ShoppingCartView.as_view(), name='shopping_cart_download'),
    path(
        'recipes/<int:recipe_id>/favorite/',
        FavoriteView.as_view(),
        name='favourite'
    ),
    path(
        'recipes/<int:recipe_id>/shopping_cart/',
        ShoppingCartView.as_view(),
        name='shopping_cart'
    ),
    path("", include(router.urls)),
]
