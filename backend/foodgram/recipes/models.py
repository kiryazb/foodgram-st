from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Кастомная модель пользователя"""

    email = models.EmailField(_("Email"), unique=True, max_length=254)
    first_name = models.CharField(_("Имя"), max_length=150)
    last_name = models.CharField(_("Фамилия"), max_length=150)
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9@.+-_]+$",
                message=_(
                    "Имя пользователя может содержать только буквы, цифры и @/./+/-/_"
                ),
                code="invalid_username",
            )
        ],
    )
    avatar = models.ImageField(
        _("Аватар"), upload_to="users/avatars/", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["email"]
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")

    def __str__(self):
        return self.email


class Subscription(models.Model):
    """Модель подписки на пользователей"""

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="followers",
    )
    author = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="authors",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_user_author"
            )
        ]
        verbose_name = _("Подписка")
        verbose_name_plural = _("Подписки")

    def __str__(self):
        return f"{self.user} подписан на {self.author}"


class Recipe(models.Model):
    """Модель рецепта"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name=_("recipes"),
        verbose_name=_("Автор"),
    )
    name = models.CharField(max_length=256, verbose_name=_("Название рецепта"))
    text = models.TextField(verbose_name=_("Описание"))
    cooking_time = models.PositiveIntegerField(
        verbose_name=_("Время приготовления (минуты)"),
        validators=[MinValueValidator(1, message=_("Минимальное время — 1 минута"))],
    )
    image = models.ImageField(upload_to="recipes/images/", verbose_name=_("Картинка"))

    ingredients = models.ManyToManyField(
        "Ingredient",
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name=_("Ингредиенты"),
    )

    class Meta:
        ordering = ("-cooking_time",)
        verbose_name = _("Рецепт")
        verbose_name_plural = _("Рецепты")

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связывающая модель для ингредиентов в рецепте"""

    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        "Ingredient",
        on_delete=models.CASCADE,
        related_name="recipe_ingredients"
    )
    amount = models.PositiveIntegerField(
        verbose_name=_("Количество"),
        validators=[MinValueValidator(1, message=_("Минимальное время — 1 минута"))]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient"
            )
        ]


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        unique=True,
        verbose_name=_("Название")
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name=_("Единица измерения")
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Ингредиент")
        verbose_name_plural = _("Ингредиенты")

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shopping_cartы"
    )
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="in_shopping_cart",
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe_in_shopping_cart"
            )
        ]
        verbose_name = _("Список покупок")
        verbose_name_plural = _("Списки покупок")

    def __str__(self):
        return f"{self.user} -> {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="in_favorites"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_user_recipe_favorite"
            )
        ]
        ordering = ["user"]

    def __str__(self):
        return f"Избранное: {self.user} – {self.recipe}"
