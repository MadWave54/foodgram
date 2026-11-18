from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')
urlpatterns = [path('', include(router.urls))]
