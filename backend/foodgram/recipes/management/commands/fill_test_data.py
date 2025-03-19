import os
import json
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Импорт данных из JSON-файла."""
        try:
            self.stdout.write(self.style.SUCCESS("Импортируем ингредиенты..."))

            base_dir = os.path.abspath(os.getcwd())
            fixture_path = os.path.join(base_dir, "data", "ingredien123ts.json")

            with open(fixture_path, encoding="utf-8") as file:
                data = json.load(file)

            ingredients_added = 0
            for item in data:
                name = item.get("name")
                measurement_unit = item.get("measurement_unit")

                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit,
                )
                if created:
                    ingredients_added += 1

            self.stdout.write(self.style.SUCCESS(f"Импорт данных завершён! Добавлено {ingredients_added} новых ингредиентов."))

        except (json.JSONDecodeError, OSError, ValidationError) as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при импорте: {e}"))
