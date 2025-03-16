import os
import json
from django.db import migrations

def load_ingredients(apps, schema_editor):
    Ingredient = apps.get_model('ingredients', 'Ingredient')

    # Получаем путь к корневой папке Django (где manage.py)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    json_path = os.path.join(BASE_DIR, "data", "ingredients.json")

    if not os.path.exists(json_path):
        print(f"❌ Файл {json_path} не найден")
        return

    with open(json_path, "r", encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)

    for item in data:
        Ingredient.objects.get_or_create(
            name=item["name"],
            measurement_unit=item["measurement_unit"]
        )

class Migration(migrations.Migration):

    dependencies = [
        ('ingredients', '0002_load_ingredients'),
    ]

    operations = [
        migrations.RunPython(load_ingredients),
    ]
