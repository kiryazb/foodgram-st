from django.urls import path

from recipes.views import get_short_link

urlpatterns = [
    path("s/<int:recipe_id>/", get_short_link, name="short_link"),
]