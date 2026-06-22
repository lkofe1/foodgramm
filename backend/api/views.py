from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Favorite, Follow, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, IngredientSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, ShortRecipeSerializer, UserWithRecipesSerializer,
    TagSerializer
)

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def _add_to_relation(self, model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        _, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                f'Рецепт "{recipe.name}" уже добавлен в '
                f'{model._meta.verbose_name}'
            )

        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _delete_from_relation(self, model, user, pk):
        get_object_or_404(model, user=user, recipe__id=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self._add_to_relation(Favorite, request.user, pk)
        return self._delete_from_relation(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self._add_to_relation(ShoppingCart, request.user, pk)
        return self._delete_from_relation(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user_recipes = Recipe.objects.filter(shoppingcarts__user=request.user)
        ingredients = RecipeIngredient.objects.filter(
            recipe__in=user_recipes
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 9: 'сентября',
            10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        today = timezone.now()
        formatted_date = f"{today.day} {months[today.month]} {today.year} г."

        shopping_list = [
            f"{i}. {item['ingredient__name'].capitalize()} "
            f"({item['ingredient__measurement_unit']}) — {item['amount']}"
            for i, item in enumerate(ingredients, start=1)
        ]

        recipes_text = "\nРецепты в списке покупок:\n"
        for recipe in user_recipes:
            tags = ", ".join(tag.name for tag in recipe.tags.all())
            author_name = recipe.author.get_full_name(
            ) or recipe.author.username
            recipes_text += (f'- {recipe.name} (Автор: {author_name}) '
                             f'[Теги: {tags}]\n')

        text = f'Список покупок {formatted_date}:\n\n' + '\n'.join(
            shopping_list) + '\n' + recipes_text

        response = HttpResponse(text, content_type='text/plain; charset=utf-8')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class UserViewSet(DjoserUserViewSet):
    pagination_class = LimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, id):
        if request.method == 'DELETE':
            get_object_or_404(
                Follow, user=request.user, author__id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = get_object_or_404(User, id=id)
        if request.user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя')

        _, created = Follow.objects.get_or_create(
            user=request.user, author=author
        )
        if not created:
            raise serializers.ValidationError(
                f'Вы уже подписаны на пользователя {author.username}'
            )

        serializer = UserWithRecipesSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[permissions.IsAuthenticated]
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = AvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
