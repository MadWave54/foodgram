from django.db.models import Sum
from django.http import HttpResponse
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart,
)
from users.models import Subscription, User

from .permissions import AuthorOrReadOnly
from .serializers import (
    AvatarSerializer, IngredientSerializer, RecipeMinifiedSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, SubscriptionSerializer,
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action in ('me', 'avatar', 'subscribe', 'subscriptions'):
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        if request.method == 'DELETE':
            request.user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            request.user, data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, **kwargs):
        author = self.get_object()
        if request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=request.user, author=author
            ).delete()
            if not deleted:
                raise serializers.ValidationError('Подписка отсутствует.')
            return Response(status=status.HTTP_204_NO_CONTENT)
        if author == request.user:
            raise serializers.ValidationError('Нельзя подписаться на себя.')
        _, created = Subscription.objects.get_or_create(
            user=request.user, author=author
        )
        if not created:
            raise serializers.ValidationError('Подписка уже существует.')
        return Response(SubscriptionSerializer(
            author, context=self.get_serializer_context()
        ).data, status=status.HTTP_201_CREATED)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name', '')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [AuthorOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'ingredient_amounts__ingredient'
        )
        if self.action != 'list':
            return queryset
        author = self.request.query_params.get('author')
        if author:
            try:
                queryset = queryset.filter(author_id=int(author))
            except ValueError:
                raise serializers.ValidationError({'author': 'Ожидается id.'})
        for parameter, model in (
            ('is_favorited', Favorite), ('is_in_shopping_cart', ShoppingCart)
        ):
            value = self.request.query_params.get(parameter)
            if value == '1':
                if not self.request.user.is_authenticated:
                    return queryset.none()
                queryset = queryset.filter(pk__in=model.objects.filter(
                    user=self.request.user
                ).values('recipe_id'))
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, **kwargs):
        recipe = self.get_object()
        path = reverse('short-link', args=[recipe.short_code])
        return Response({'short-link': request.build_absolute_uri(path)})

    def change_collection(self, request, model):
        recipe = self.get_object()
        if request.method == 'DELETE':
            deleted, _ = model.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
            if not deleted:
                raise serializers.ValidationError('Рецепт отсутствует в списке.')
            return Response(status=status.HTTP_204_NO_CONTENT)
        _, created = model.objects.get_or_create(user=request.user, recipe=recipe)
        if not created:
            raise serializers.ValidationError('Рецепт уже добавлен.')
        return Response(RecipeMinifiedSerializer(
            recipe, context=self.get_serializer_context()
        ).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, **kwargs):
        return self.change_collection(request, Favorite)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        return self.change_collection(request, ShoppingCart)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        rows = RecipeIngredient.objects.filter(
            recipe__shoppingcart__user=request.user
        ).values('ingredient__name', 'ingredient__measurement_unit').annotate(
            total=Sum('amount')
        ).order_by('ingredient__name')
        lines = ['Список покупок — Фудграм', '']
        lines.extend(
            f"{row['ingredient__name']} "
            f"({row['ingredient__measurement_unit']}) — {row['total']}"
            for row in rows
        )
        response = HttpResponse(
            '\n'.join(lines), content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="shopping-list.txt"'
        return response
