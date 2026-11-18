import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


def generate_short_code():
    return secrets.token_urlsafe(8)


class Ingredient(models.Model):
    name = models.CharField(max_length=128, db_index=True)
    measurement_unit = models.CharField(max_length=64)

    class Meta:
        ordering = ['name', 'id']
        constraints = [models.UniqueConstraint(
            fields=['name', 'measurement_unit'], name='unique_ingredient'
        )]
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', related_name='recipes'
    )
    cooking_time = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    short_code = models.CharField(
        max_length=16, unique=True, default=generate_short_code, editable=False
    )

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [models.CheckConstraint(
            condition=models.Q(cooking_time__gte=1), name='positive_cooking_time'
        )]
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredient_amounts'
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'], name='unique_recipe_ingredient'
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=1), name='positive_amount'
            ),
        ]
        verbose_name = 'ингредиент рецепта'
        verbose_name_plural = 'Состав рецептов'

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class UserRecipe(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'], name='%(class)s_unique_user_recipe'
        )]

    def __str__(self):
        return f'{self.user}: {self.recipe}'


class Favorite(UserRecipe):
    class Meta(UserRecipe.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipe):
    class Meta(UserRecipe.Meta):
        verbose_name = 'покупка'
        verbose_name_plural = 'Список покупок'
