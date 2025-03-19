from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее редактировать объект только его автору,
    а читать — всем остальным.
    """
    def has_permission(self, request, view):
        # Разрешаем доступ всем к чтению (list, retrieve) и аутентифицированным к созданию
        # (логика при необходимости может меняться).
        # Если нужна более тонкая настройка — можно передавать в get_permissions разные пермишены.
        return True

    def has_object_permission(self, request, view, obj):
        # Для безопасных методов (GET, HEAD, OPTIONS) разрешаем доступ всем.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для небезопасных методов (POST, PATCH, DELETE) проверяем автора.
        return obj.author == request.user