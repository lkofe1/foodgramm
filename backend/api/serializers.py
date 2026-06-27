import base64
from collections import Counter

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag,
    Follow, MIN_AMOUNT, MIN_COOKING_TIME
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr), name='temp.' + ext
            )
        return super().to_internal_value(data)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed',
            'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Follow.objects.filter(
                user=request.user, author=author
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image',
            'text', 'cooking_time'
        )
        read_only_fields = fields

    def _check_relation(self, recipe, model):
        request = self.context.get('request')
        # Убран вызов bool(). Логические операторы (and) и метод .exists()
        # уже возвращают булево значение.
        return (
            request is not None
            and request.user.is_authenticated
            and model.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self._check_relation(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._check_relation(recipe, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text',
            'cooking_time', 'author'
        )

    def _check_duplicates(self, items, field_name):
        duplicates = [
            item for item, count in Counter(items).items() if count > 1
        ]
        if duplicates:
            raise serializers.ValidationError(
                f'Дублирующиеся {field_name}: {duplicates}'
            )

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Нужен хотя бы один ингредиент.'
            )

        self._check_duplicates(
            [item['id'] for item in ingredients], 'ингредиенты'
        )

        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError('Нужен хотя бы один тег.')

        self._check_duplicates(tags, 'теги')

        return data

    def create_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ) for item in ingredients
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.set(validated_data.pop('tags'))
        instance.recipe_ingredients.all().delete()
        self.create_ingredients(
            instance, validated_data.pop('ingredients')
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context=self.context
        ).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = (
            *UserSerializer.Meta.fields,
            'recipes',
            'recipes_count'
        )
        read_only_fields = fields

    def get_recipes(self, author):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit') if request else None
        recipes = author.recipes.all()
        if limit:
            try:
                recipes = recipes[:int(limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context
        ).data
