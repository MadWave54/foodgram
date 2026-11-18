import base64
import tempfile
from io import BytesIO

from django.test import override_settings
from PIL import Image
from rest_framework.test import APITestCase

from recipes.models import Ingredient, Recipe, RecipeIngredient, ShoppingCart
from users.models import Subscription, User


class FoodgramIntegrationTests(APITestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.media.cleanup)
        self.addCleanup(self.override.disable)
        self.author = User.objects.create_user(
            username='author', email='author@example.com', password='Test-pass-123'
        )
        self.reader = User.objects.create_user(
            username='reader', email='reader@example.com', password='Test-pass-123'
        )
        self.ingredient = Ingredient.objects.create(
            name='Картофель', measurement_unit='г'
        )
        self.recipe = Recipe.objects.create(
            author=self.author, name='Первый рецепт', text='Приготовить',
            cooking_time=10, image='recipes/test.png',
        )
        RecipeIngredient.objects.create(
            recipe=self.recipe, ingredient=self.ingredient, amount=100
        )

    def payload(self):
        buffer = BytesIO()
        Image.new('RGB', (10, 10)).save(buffer, format='PNG')
        return {
            'name': 'Новый рецепт', 'text': 'Приготовить', 'cooking_time': 15,
            'image': 'data:image/png;base64,' + base64.b64encode(
                buffer.getvalue()
            ).decode(),
            'ingredients': [{'id': self.ingredient.pk, 'amount': 75}],
        }

    def test_cart_aggregates_shared_ingredients_and_is_user_scoped(self):
        second = Recipe.objects.create(
            author=self.author, name='Второй рецепт', text='Приготовить',
            cooking_time=20, image='recipes/test2.png',
        )
        RecipeIngredient.objects.create(
            recipe=second, ingredient=self.ingredient, amount=250
        )
        for recipe in (self.recipe, second):
            ShoppingCart.objects.create(user=self.reader, recipe=recipe)
        ShoppingCart.objects.create(user=self.author, recipe=second)
        self.client.force_authenticate(self.reader)
        response = self.client.get('/api/recipes/download_shopping_cart/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Картофель (г) — 350', response.content.decode())
        self.assertEqual(response.content.decode().count('Картофель'), 1)

    def test_write_permissions_and_ingredient_replacement(self):
        url = f'/api/recipes/{self.recipe.pk}/'
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.patch(url, self.payload(), format='json').status_code, 403)
        self.client.force_authenticate(self.author)
        self.assertEqual(self.client.patch(url, self.payload(), format='json').status_code, 200)
        self.assertEqual(self.recipe.ingredient_amounts.get().amount, 75)

    def test_invalid_duplicate_ingredients_leave_recipe_unchanged(self):
        self.client.force_authenticate(self.author)
        payload = self.payload()
        payload['ingredients'] *= 2
        response = self.client.patch(
            f'/api/recipes/{self.recipe.pk}/', payload, format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, 'Первый рецепт')
        self.assertEqual(self.recipe.ingredient_amounts.get().amount, 100)

    def test_short_link_is_stable_and_redirects(self):
        url = f'/api/recipes/{self.recipe.pk}/get-link/'
        first = self.client.get(url).data['short-link']
        self.assertEqual(first, self.client.get(url).data['short-link'])
        response = self.client.get(first)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], f'/recipes/{self.recipe.pk}')

    def test_subscription_rejects_self_and_duplicates(self):
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.post(
            f'/api/users/{self.reader.pk}/subscribe/'
        ).status_code, 400)
        url = f'/api/users/{self.author.pk}/subscribe/'
        self.assertEqual(self.client.post(url).status_code, 201)
        self.assertEqual(self.client.post(url).status_code, 400)
        self.assertEqual(Subscription.objects.count(), 1)

    def test_token_login_and_logout(self):
        response = self.client.post('/api/auth/token/login/', {
            'email': self.reader.email, 'password': 'Test-pass-123',
        })
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['auth_token'])
        self.assertEqual(self.client.get('/api/users/me/').status_code, 200)
        self.assertEqual(self.client.post('/api/auth/token/logout/').status_code, 204)
        self.assertEqual(self.client.get('/api/users/me/').status_code, 401)
