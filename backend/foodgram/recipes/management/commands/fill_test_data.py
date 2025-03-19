from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()


class Command(BaseCommand):
    help = "Импортирует данные из фикстуры"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Импортируем ингредиенты..."))
        call_command("loaddata", "data/ingredients.json")  # ✅ Загружаем фикстуру

        self.stdout.write(self.style.SUCCESS("Импорт данных завершён!"))
