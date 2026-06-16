import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из папки data в базу данных'

    def handle(self, *args, **options):

        path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')

        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(
                f'Файл не найден по пути: {path}'))
            return

        self.stdout.write('Начало загрузки ингредиентов...')

        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            ingredients_to_create = []

            for item in data:
                ingredients_to_create.append(
                    Ingredient(
                        name=item['name'],
                        measurement_unit=item['measurement_unit']
                    )
                )

            Ingredient.objects.bulk_create(
                ingredients_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f'Успешно загружено ингредиентов: {len(ingredients_to_create)}!'))
