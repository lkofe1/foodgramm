from recipes.management.base_import import BaseJsonImportCommand
from recipes.models import Ingredient


class Command(BaseJsonImportCommand):
    help = 'Загрузка ингредиентов из папки data в базу данных'
    filename = 'ingredients.json'
    model = Ingredient
