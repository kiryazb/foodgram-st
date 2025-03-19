from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_cart"
    )
    recipe = models.ForeignKey(
        "recipes.Recipe",  # Указать путь до модели Recipe
        on_delete=models.CASCADE,
        related_name="in_shopping_cart",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe_in_shopping_cart"
            )
        ]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"

    def __str__(self):
        return f"{self.user} -> {self.recipe}"
