from recipes.management.base_import import BaseJsonImportCommand
from recipes.models import Tag


class Command(BaseJsonImportCommand):
    help = 'Загрузка тегов из папки data в базу данных'
    filename = 'tags.json'
    model = Tag
    label = 'тегов'
