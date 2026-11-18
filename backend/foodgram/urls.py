from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.urls import include, path

from recipes.models import Recipe


def short_link(request, code):
    recipe = get_object_or_404(Recipe, short_code=code)
    return redirect(f'/recipes/{recipe.pk}')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('s/<str:code>/', short_link, name='short-link'),
]
