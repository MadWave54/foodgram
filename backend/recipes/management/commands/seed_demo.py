from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from recipes.models import Ingredient, Recipe, RecipeIngredient
from users.models import User


class Command(BaseCommand):
    help = 'Создать демонстрационных пользователей и восемь рецептов.'

    def handle(self, *args, **options):
        call_command('load_ingredients')
        users = []
        for username, first, last, is_staff in [
            ('admin', 'Администратор', 'Фудграма', True),
            ('matvey', 'Матвей', 'Карпенко', False),
            ('anna', 'Анна', 'Петрова', False),
        ]:
            user, created = User.objects.get_or_create(
                email=f'{username}@foodgram.local', defaults={
                    'username': username, 'first_name': first,
                    'last_name': last, 'is_staff': is_staff,
                    'is_superuser': is_staff,
                }
            )
            if created:
                user.set_password('Foodgram-Demo-2026')
                user.save()
            users.append(user)
        recipes = [
            ('Овсяная каша с фруктами', 15, 'овсяные хлопья', 'молоко', 80, 200),
            ('Нежный омлет', 10, 'яйца куриные', 'молоко', 3, 60),
            ('Картофельное пюре', 30, 'картофель', 'молоко', 600, 150),
            ('Рисовая каша', 25, 'рис', 'молоко', 100, 300),
            ('Домашние блины', 35, 'мука', 'молоко', 200, 400),
            ('Овощной салат', 10, 'помидоры', 'огурцы', 250, 200),
            ('Запечённый картофель', 45, 'картофель', 'оливковое масло', 500, 30),
            ('Сырники к завтраку', 25, 'творог', 'мука', 400, 60),
        ]
        for index, (name, minutes, first, second, a, b) in enumerate(recipes):
            author = users[index % len(users)]
            if Recipe.objects.filter(name=name, author=author).exists():
                continue
            recipe = Recipe(
                name=name, author=author, cooking_time=minutes,
                text=(f'Подготовьте ингредиенты для блюда «{name}». '
                      'Вымойте и отмерьте продукты. Смешайте ингредиенты, '
                      'приготовьте до готовности и подавайте тёплым. '
                      'Количество продуктов указано на две порции.'),
            )
            image = Image.new('RGB', (960, 640), '#f3e9db')
            draw = ImageDraw.Draw(image)
            draw.ellipse((190, 40, 770, 620), fill='#ffffff', outline='#ded6ca', width=8)
            colors = ['#dcb264', '#ecc44d', '#e5ca85', '#e9d4ac',
                      '#d1a268', '#77a84a', '#d6a03c', '#e8b75c']
            draw.ellipse((275, 125, 685, 535), fill=colors[index])
            for x, y in [(370, 240), (520, 320), (440, 420)]:
                draw.ellipse((x, y, x + 50, y + 35), fill='#b85038')
                draw.ellipse((x + 25, y - 20, x + 60, y), fill='#5c8545')
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            recipe.image.save(f'demo-{index}.png', ContentFile(buffer.getvalue()))
            for ingredient_name, amount in [(first, a), (second, b)]:
                ingredient = Ingredient.objects.filter(
                    name__iexact=ingredient_name
                ).first()
                if ingredient is None:
                    ingredient, _ = Ingredient.objects.get_or_create(
                        name=ingredient_name, measurement_unit='г'
                    )
                RecipeIngredient.objects.create(
                    recipe=recipe, ingredient=ingredient, amount=amount
                )
        self.stdout.write(self.style.SUCCESS(
            'Демо готово. Пароль новых аккаунтов: Foodgram-Demo-2026'
        ))
