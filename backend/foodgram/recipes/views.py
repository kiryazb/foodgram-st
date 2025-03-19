from django.shortcuts import get_object_or_404, redirect
from .models import Recipe

def get_short_link(request, recipe_id):
    """
    Обрабатывает короткую ссылку и перенаправляет на локальный URL рецепта.
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Формируем URL на локальном сервере
    full_url = f"http://localhost:80/recipes/{recipe.id}/"

    return redirect(full_url)