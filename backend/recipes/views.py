from django.shortcuts import redirect, get_object_or_404
from recipes.models import Recipe


def recipe_short_link_redirect(request, pk):
    get_object_or_404(Recipe, pk=pk)
    return redirect(f'/recipes/{pk}/')
