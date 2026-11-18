from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (('Аватар', {'fields': ('avatar',)}),)


admin.site.register(Subscription)
