from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Кастомная модель пользователя"""

    email = models.EmailField(_("Email"), unique=True, max_length=254)
    first_name = models.CharField(_("Имя"), max_length=150)
    last_name = models.CharField(_("Фамилия"), max_length=150)
    username = models.CharField(
        _("Имя пользователя"),
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
        ordering = ["id"]
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
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=256, verbose_name="Название рецепта")
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления (минуты)",
        validators=[MinValueValidator(1, message="Минимальное время — 1 минута")],
    )
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Картинка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    ingredients = models.ManyToManyField(
        "Ingredient",
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Связующая модель для ингредиентов в рецепте"""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        "Ingredient", on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1, message="Минимальное время — 1 минута")],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"], name="unique_recipe_ingredient"
            )
        ]


class Ingredient(models.Model):
    name = models.CharField(max_length=128, unique=True, verbose_name="Название")
    measurement_unit = models.CharField(max_length=64, verbose_name="Единица измерения")

    class Meta:
        ordering = ["name"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"
