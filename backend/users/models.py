from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, max_length=254)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to='users/', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_subscription'
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='no_self_subscription',
            ),
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user} → {self.author}'
