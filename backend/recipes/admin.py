from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)

User = get_user_model()


class RecipeCountMixin:
    list_display: tuple[str, ...] = ('get_recipes_count',)

    @admin.display(description='Рецепты')
    def get_recipes_count(self, instance):
        return instance.recipes.count()


@admin.register(User)
class UserAdmin(RecipeCountMixin, BaseUserAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name',
        'get_avatar', *RecipeCountMixin.list_display, 'get_subscribers_count',
        'get_subscriptions_count'
    )
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_active')

    @admin.display(description='Аватар')
    def get_avatar(self, user):
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" width="50" height="50" '
                f'style="border-radius: 50%; object-fit: cover;"/>'
            )
        return 'Нет фото'

    @admin.display(description='Подписчики')
    def get_subscribers_count(self, user):
        return user.subscribers.count()

    @admin.display(description='Подписки')
    def get_subscriptions_count(self, user):
        return user.subscriptions.count()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time', 'get_favorites_count',
        'get_ingredients', 'get_image'
    )
    list_filter = ('tags', 'author')
    search_fields = (
        'name', 'author__username', 'tags__name', 'ingredients__name'
    )
    inlines = (RecipeIngredientInline,)

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipe):
        return recipe.in_favorites.count()

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, recipe):
        return mark_safe('<br>'.join(
            f'{item.ingredient.name} ({item.amount} '
            f'{item.ingredient.measurement_unit})'
            for item in recipe.recipe_ingredients.all()
        ))

    @admin.display(description='Картинка')
    def get_image(self, recipe):
        if recipe.image:
            return mark_safe(
                f'<img src="{recipe.image.url}" width="50" height="50" '
                f'style="object-fit: cover;"/>'
            )
        return 'Нет картинки'


@admin.register(Ingredient)
class IngredientAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = (
        'id', 'name', 'measurement_unit', *RecipeCountMixin.list_display
    )
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', *RecipeCountMixin.list_display)
    search_fields = ('name', 'slug')



@admin.register(Favorite, ShoppingCart)
class RecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
