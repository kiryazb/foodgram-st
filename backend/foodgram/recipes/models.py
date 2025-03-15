from django.db import models
from django.contrib.auth import get_user_model
from ingredients.models import Ingredient

User = get_user_model()

class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор"
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название рецепта"
    )
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveIntegerField(verbose_name="Время приготовления (минуты)")
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Картинка")

    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты"
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связующая модель для ингредиентов в рецепте"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_recipes"
    )
    amount = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient"
            )
        ]
