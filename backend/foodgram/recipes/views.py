from django.shortcuts import redirect, get_object_or_404

from recipes.models import Recipe


def get_short_link(request, recipe_id):
    """
    Обрабатывает короткую ссылку и перенаправляет на локальный URL рецепта.
    """
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f"/recipes/{recipe_id}/")
