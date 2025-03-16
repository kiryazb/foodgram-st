from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""

    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
    )
    avatar = models.ImageField(upload_to="users/avatars/", null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.email


class Subscription(models.Model):
    """Модель подписки на пользователей"""

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="followers"
    )
    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="following"
    )

    class Meta:
        # Один пользователь может подписаться только 1 раз
        unique_together = ("user", "author")

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
