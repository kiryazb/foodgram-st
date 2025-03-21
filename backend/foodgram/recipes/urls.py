from django.urls import path

from recipes.views import get_short_link

app_name = "recipes"

urlpatterns = [
    path("s/<int:recipe_id>/", get_short_link, name="short_link"),
]
