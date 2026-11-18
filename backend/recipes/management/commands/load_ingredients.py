import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузить ингредиенты из JSON без повторного создания записей.'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=Path)

    def handle(self, *args, **options):
        path = options['path'] or settings.BASE_DIR / 'data' / 'ingredients.json'
        if not path.exists():
            path = settings.BASE_DIR.parent / 'data' / 'ingredients.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        Ingredient.objects.bulk_create(
            [Ingredient(**row) for row in data], ignore_conflicts=True
        )
        self.stdout.write(self.style.SUCCESS(
            f'Ингредиентов в базе: {Ingredient.objects.count()}'
        ))
