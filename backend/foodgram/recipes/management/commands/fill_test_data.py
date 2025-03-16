import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from favorites.models import Favorite
from ingredients.models import Ingredient
from recipes.models import Recipe, RecipeIngredient
from shopping_cart.models import ShoppingCart
from subscribers.models import Subscription

User = get_user_model()

TEST_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "adminpass",
        "is_superuser": True,
        "is_staff": True,
    },
    {"email": "user1@example.com", "username": "user1", "password": "userpass"},
    {"email": "user2@example.com", "username": "user2", "password": "userpass"},
]

TEST_INGREDIENTS = [
    {"name": "Сахар", "measurement_unit": "г"},
    {"name": "Молоко", "measurement_unit": "мл"},
    {"name": "Яйцо", "measurement_unit": "шт"},
    {"name": "Мука", "measurement_unit": "г"},
]

TEST_RECIPES = [
    {"name": "Блины", "text": "Вкусные домашние блины", "cooking_time": 15},
    {"name": "Каша", "text": "Овсяная каша на молоке", "cooking_time": 10},
    {"name": "Омлет", "text": "Классический омлет с молоком", "cooking_time": 7},
]


class Command(BaseCommand):
    help = "Создаёт тестовых пользователей, ингредиенты и рецепты"

    def handle(self, *args, **kwargs):
        self.stdout.write("Создаём пользователей...")
        users = []
        for user_data in TEST_USERS:
            user = User.objects.filter(username=user_data["username"]).first()
            if user:
                self.stdout.write(
                    f"Пользователь {user.username} уже существует, пропускаем."
                )
            else:
                try:
                    user = User.objects.create(**user_data)
                    user.set_password(user_data["password"])
                    user.save()
                    self.stdout.write(f"Создан пользователь {user.username}.")
                except IntegrityError:
                    self.stdout.write(
                        f"Ошибка: пользователь {user_data['username']} уже существует, пропускаем."
                    )
                    continue  # Пропускаем создание дубликатов
            users.append(user)

        self.stdout.write("Создаём ингредиенты...")
        ingredients = []
        for ing_data in TEST_INGREDIENTS:
            ingredient, created = Ingredient.objects.get_or_create(**ing_data)
            ingredients.append(ingredient)

        self.stdout.write("Создаём рецепты...")
        for user, recipe_data in zip(users, TEST_RECIPES):
            recipe, created = Recipe.objects.get_or_create(
                author=user, defaults=recipe_data
            )
            if created:
                selected_ingredients = random.sample(ingredients, k=2)
                for ingredient in selected_ingredients:
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=random.randint(1, 500),
                    )

        self.stdout.write("Создаём избранное и список покупок...")
        for user in users:
            random_recipe = random.choice(Recipe.objects.all())
            Favorite.objects.get_or_create(user=user, recipe=random_recipe)
            ShoppingCart.objects.get_or_create(user=user, recipe=random_recipe)

        self.stdout.write("Создаём подписки...")
        for user in users:
            for other_user in users:
                if (
                    user != other_user
                    and not Subscription.objects.filter(
                        user=user, author=other_user
                    ).exists()
                ):
                    Subscription.objects.create(user=user, author=other_user)

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно созданы!"))
