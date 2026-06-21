from django.shortcuts import redirect
from rest_framework.exceptions import ValidationError

from recipes.models import Recipe


def recipe_short_link_redirect(request, pk):
    if not Recipe.objects.filter(pk=pk).exists():
        raise ValidationError(f'Рецепт с id {pk} не найден')

    return redirect(f'/recipes/{pk}/')
