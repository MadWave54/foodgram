import base64
import binascii
import uuid

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
)
from users.models import Subscription, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image/'):
            try:
                header, encoded = data.split(';base64,', 1)
                extension = header.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(encoded, validate=True),
                    name=f'{uuid.uuid4().hex}.{extension}',
                )
            except (ValueError, binascii.Error):
                raise serializers.ValidationError('Некорректное изображение.')
        return super().to_internal_value(data)


class RegisterSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and Subscription.objects.filter(
            user=user, author=obj
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class AmountReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AmountWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1, max_value=2147483647)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = AmountReadSerializer(source='ingredient_amounts', many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def user_relation_exists(self, model, obj):
        user = self.context['request'].user
        return user.is_authenticated and model.objects.filter(
            user=user, recipe=obj
        ).exists()

    def get_is_favorited(self, obj):
        return self.user_relation_exists(Favorite, obj)

    def get_is_in_shopping_cart(self, obj):
        return self.user_relation_exists(ShoppingCart, obj)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = AmountWriteSerializer(many=True, allow_empty=False)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1, max_value=2147483647)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'image', 'name', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        ids = [row['id'].pk for row in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться.')
        return value

    def validate(self, attrs):
        for field in ('ingredients', 'name', 'text', 'cooking_time'):
            if field not in attrs:
                raise serializers.ValidationError({field: 'Обязательное поле.'})
        return attrs

    def save_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe, ingredient=row['id'], amount=row['amount']
            ) for row in ingredients
        ])

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.save_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.ingredient_amounts.all().delete()
        self.save_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        limit = self.context['request'].query_params.get('recipes_limit')
        if limit is not None:
            try:
                limit = int(limit)
                if limit < 0:
                    raise ValueError
            except ValueError:
                raise serializers.ValidationError(
                    {'recipes_limit': 'Ожидается неотрицательное целое число.'}
                )
            recipes = recipes[:limit]
        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context
        ).data
