from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

MIN_COOKING_TIME = 1
MIN_AMOUNT = 1


class User(AbstractUser):
    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True,
        validators=[RegexValidator(
            regex=settings.USERNAME_REGEX
        )]
    )
    email = models.EmailField('Email', max_length=254, unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар', upload_to='users/', null=True, default=None
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Tag(models.Model):
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField('Слаг', max_length=32, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название', max_length=128)
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор'
    )
    name = models.CharField('Название', max_length=128)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления', validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f'Минимальное время {MIN_COOKING_TIME} минута'
            )
        ]
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(
            MIN_AMOUNT, message=f'Минимальное количество — {MIN_AMOUNT}'
        )]
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class UserRecipeRelation(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(class)s'
            )
        ]


class Favorite(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='no_self_follow'
            )
        ]
