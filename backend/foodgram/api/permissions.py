from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrReadOnly(BasePermission):
    """
    Разрешение: читать могут все, редактировать — только автор.
    """
    message = "Вы не являетесь автором данного рецепта."

    def has_object_permission(self, request, view, obj):
        # Безопасные методы (GET, HEAD, OPTIONS) разрешены всем.
        if request.method in SAFE_METHODS:
            return True
        # На изменения — только автор
        return obj.author == request.user