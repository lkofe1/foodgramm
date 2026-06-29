from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe


def recipe_short_link_redirect(request, pk):
    if Recipe.objects.filter(pk=pk).exists():
        return redirect(f'/recipes/{pk}/')

    raise Http404(f'Рецепт с ID {pk} не найден')
