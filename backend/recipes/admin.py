from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag)

User = get_user_model()

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorites_count')
    list_filter = ('tags', 'author', 'name')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = (RecipeIngredientInline,)

    @admin.display(description='Добавлений в избранное')
    def get_favorites_count(self, obj):
        return obj.in_favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


admin.site.register(Tag)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
