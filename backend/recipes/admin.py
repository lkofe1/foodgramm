from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)

User = get_user_model()

admin.site.unregister(Group)


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'Наличие рецептов'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (('1', 'Есть рецепты'), ('0', 'Нет рецептов'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.annotate(rc=Count('recipes')).filter(rc__gt=0)
        if self.value() == '0':
            return queryset.annotate(rc=Count('recipes')).filter(rc=0)
        return queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return (('1', 'Есть подписчики'), ('0', 'Нет подписчиков'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.annotate(sc=Count('following')).filter(sc__gt=0)
        if self.value() == '0':
            return queryset.annotate(sc=Count('following')).filter(sc=0)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = 'Наличие подписок'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (('1', 'Есть подписки'), ('0', 'Нет подписок'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.annotate(sc=Count('follower')).filter(sc__gt=0)
        if self.value() == '0':
            return queryset.annotate(sc=Count('follower')).filter(sc=0)
        return queryset


class InRecipeFilter(admin.SimpleListFilter):
    title = 'Использование в рецептах'
    parameter_name = 'in_recipes'

    def lookups(self, request, model_admin):
        return (('1', 'Есть в рецептах'), ('0', 'Нет в рецептах'))

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.annotate(rc=Count('recipes')).filter(rc__gt=0)
        if self.value() == '0':
            return queryset.annotate(rc=Count('recipes')).filter(rc=0)
        return queryset


class RecipeCountMixin:
    list_display: tuple[str, ...] = ('get_recipes_count',)

    @admin.display(description='Рецепты')
    def get_recipes_count(self, instance):
        return instance.recipes.count()


@admin.register(User)
class UserAdmin(RecipeCountMixin, BaseUserAdmin):
    list_display = (
        'id', 'username', 'email', 'get_fio',
        'get_avatar', *RecipeCountMixin.list_display, 'get_subscribers_count',
        'get_subscriptions_count'
    )
    search_fields = ('email', 'username')
    list_filter = (
        'is_staff', 'is_active', HasRecipesFilter,
        HasSubscriptionsFilter, HasSubscribersFilter
    )
    empty_value_display = '-'

    @admin.display(description='ФИО')
    def get_fio(self, user):
        return f"{user.first_name} {user.last_name}".strip() or None

    @admin.display(description='Аватар')
    def get_avatar(self, user):
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" width="50" height="50" '
                f'style="border-radius: 50%; object-fit: cover;"/>'
            )
        return None

    @admin.display(description='Подписчики')
    def get_subscribers_count(self, user):
        return user.following.count()

    @admin.display(description='Подписки')
    def get_subscriptions_count(self, user):
        return user.follower.count()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    empty_value_display = '-'


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
    empty_value_display = '-'

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipe):
        return recipe.favorites.count()

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
        return None


@admin.register(Ingredient)
class IngredientAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = (
        'id', 'name', 'measurement_unit', *RecipeCountMixin.list_display
    )
    search_fields = ('name',)
    list_filter = ('measurement_unit', InRecipeFilter)
    empty_value_display = '-'


@admin.register(Tag)
class TagAdmin(RecipeCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', *RecipeCountMixin.list_display)
    search_fields = ('name', 'slug')
    empty_value_display = '-'


@admin.register(Favorite, ShoppingCart)
class RecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    empty_value_display = '-'
