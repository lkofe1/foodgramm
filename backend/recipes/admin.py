from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)

User = get_user_model()

admin.site.unregister(Group)


class BasePresenceFilter(admin.SimpleListFilter):
    """Базовый класс для фильтров по наличию связанных объектов."""
    filter_field: str = ''
    LABELS = {'true': 'Есть', 'false': 'Нет'}

    def lookups(self, request, model_admin):
        item_name = self.title.split()[-1]
        return (
            ('1', f'{self.LABELS["true"]} {item_name}'),
            ('0', f'{self.LABELS["false"]} {item_name}')
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(
                **{f'{self.filter_field}__isnull': False}
            ).distinct()
        if self.value() == '0':
            return queryset.filter(
                **{f'{self.filter_field}__isnull': True}
            )
        return queryset


class HasRecipesFilter(BasePresenceFilter):
    title = 'Наличие рецептов'
    parameter_name = 'has_recipes'
    filter_field = 'recipes'


class HasSubscribersFilter(BasePresenceFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'has_subscribers'
    filter_field = 'following'


class HasSubscriptionsFilter(BasePresenceFilter):
    title = 'Наличие подписок'
    parameter_name = 'has_subscriptions'
    filter_field = 'follower'


class InRecipeFilter(BasePresenceFilter):
    title = 'Использование в рецептах'
    parameter_name = 'in_recipes'
    filter_field = 'recipes'


class RecipeCountMixin:
    list_display: tuple[str, ...] = ('get_recipes_count',)

    @admin.display(description='Рецепты')
    def get_recipes_count(self, instance):
        return instance.recipes.count()


@admin.register(User)
class UserAdmin(RecipeCountMixin, BaseUserAdmin):
    list_display = (
        'id', 'username', 'email', 'get_fio', 'get_avatar',
        *RecipeCountMixin.list_display, 'get_subscribers_count',
        'get_subscriptions_count'
    )
    search_fields = ('email', 'username')
    list_filter = (
        'is_staff', 'is_active', HasRecipesFilter,
        HasSubscriptionsFilter, HasSubscribersFilter
    )

    readonly_fields = ('avatar_preview',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar', 'avatar_preview')}),
    )
    empty_value_display = '-'

    @admin.display(description='ФИО')
    def get_fio(self, user):
        return f'{user.first_name} {user.last_name}'.strip() or None

    @admin.display(description='Аватар')
    def get_avatar(self, user):
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" width="50" height="50" '
                f'style="border-radius: 50%; object-fit: cover;"/>'
            )
        return ''

    @admin.display(description='Текущий аватар')
    def avatar_preview(self, user):
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" style="max-height: 150px; '
                f'max-width: 150px; object-fit: cover; border-radius: 50%; '
                f'box-shadow: 0 2px 4px rgba(0,0,0,0.15);"/>'
            )
        return 'Аватар не установлен'

    @admin.display(description='Подписчики')
    def get_subscribers_count(self, user):
        return user.follower.count()

    @admin.display(description='Подписки')
    def get_subscriptions_count(self, user):
        return user.following.count()


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
        'id', 'name', 'author', 'get_cooking_time_display',
        'get_tags', 'get_favorites_count', 'get_image'
    )
    list_filter = ('tags', 'author')
    search_fields = (
        'name', 'author__username', 'tags__name', 'ingredients__name'
    )
    inlines = (RecipeIngredientInline,)
    empty_value_display = '-'

    readonly_fields = ('image_preview',)

    @admin.display(description='Просмотр картинки')
    def image_preview(self, recipe):
        if recipe.image:
            return mark_safe(
                f'<img src="{recipe.image.url}" style="max-height: 200px; '
                f'max-width: 300px; object-fit: contain; border-radius: 4px;">'
            )
        return None

    @admin.display(description=mark_safe('Время<br>приготовления (мин)'))
    def get_cooking_time_display(self, obj):
        return obj.cooking_time

    @admin.display(description='Теги')
    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])

    @admin.display(description='В избранном')
    def get_favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Картинка')
    def get_image(self, recipe):
        if recipe.image:
            return mark_safe(
                f'<img src="{recipe.image.url}" width="100" '
                f'style="object-fit: cover;"/>'
            )
        return ''


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
