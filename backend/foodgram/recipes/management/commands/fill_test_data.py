import os
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Импортирует данные из фикстуры"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Импортируем ингредиенты..."))

        # Получаем абсолютный путь к директории, где выполняется скрипт
        base_dir = os.path.abspath(os.getcwd())
        fixture_path = os.path.join(base_dir, "data", "ingredients.json")

        # Вывод абсолютного пути (для отладки)
        self.stdout.write(self.style.WARNING(f"Ищем файл по пути: {fixture_path}"))

        # Проверяем, существует ли файл
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.ERROR(f"Фикстура {fixture_path} не найдена!"))
            return

        call_command("loaddata", fixture_path)

        self.stdout.write(self.style.SUCCESS("Импорт данных завершён!"))
