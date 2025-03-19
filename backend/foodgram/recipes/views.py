from django.shortcuts import redirect


def get_short_link(request, recipe_id):
    """
    Обрабатывает короткую ссылку и перенаправляет на локальный URL рецепта.
    """

    return redirect(request.build_absolute_uri(f"/recipes/{recipe_id}/"))
