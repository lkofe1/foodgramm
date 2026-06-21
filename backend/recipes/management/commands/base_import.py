import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand


class BaseJsonImportCommand(BaseCommand):

    filename = None
    model = None

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'data', self.filename)
        self.stdout.write(f'Начало загрузки из файла {self.filename}...')

        try:
            with open(path, 'r', encoding='utf-8') as file:
                data_to_create = (
                    self.model(**item) for item in json.load(file)
                )
                created_items = self.model.objects.bulk_create(
                    data_to_create, ignore_conflicts=True
                )

            self.stdout.write(self.style.SUCCESS(
                f'Успешно загружено: {len(created_items)} '
                f'из файла {self.filename}!'
            ))
        except Exception as error:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при загрузке данных из {self.filename}: {error}'
            ))
