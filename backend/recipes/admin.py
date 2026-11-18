from django.contrib import admin
from django.db.models import Count

from .models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart


class IngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'cooking_time', 'favorite_count')
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('favorite_count', 'short_code', 'created_at')
    inlines = (IngredientInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            favorites_total=Count('favorite', distinct=True)
        )

    @admin.display(description='Добавлений в избранное')
    def favorite_count(self, obj):
        return obj.favorites_total


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register([RecipeIngredient, Favorite, ShoppingCart])
