""" test ingredients api """
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Ingredient,Recipe
from recipe.serializers import IngredientSerializer
from decimal import Decimal

INGREDIENTS_URL = reverse('recipe:ingredient-list')

def detail_url(ingredient_id):
        return reverse('recipe:ingredient-detail',args=[ingredient_id])

def create_user(email='test@example.com',password='test12345'):
    return get_user_model().objects.create_user(email=email,password=password)


class PublicIngredientsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')
        res = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        user2 = create_user(email='test2@example.com')
        ingredient = Ingredient.objects.create(user=self.user, name='Veggie')
        Ingredient.objects.create(user=user2, name='Fruit')
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'],ingredient.name)
        self.assertEqual(res.data[0]['id'],ingredient.id)

    def test_update_ingredient(self):
        """test updating an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user,name="ing1")
        payload = {
            'name':'new ing'
        }
        url = detail_url(ingredient.id)
        res = self.client.patch(url,payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name,payload['name'])

    def test_delete_ingredient(self):
        """delete an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user,name='ing1')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """test filtering ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Ingredient 1')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Ingredient 2')
        recipe = Recipe.objects.create(title='Recipe 1', time_minutes=10, user=self.user,price=Decimal('10.3'))
        recipe_ingredients = recipe.ingredients.add(ingredient1)
        res = self.client.get(INGREDIENTS_URL,{'assigned_only':1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data,res.data)
        self.assertNotIn(serializer2.data,res.data)

    def test_filtered_ingredients_unique(self):
        """test filtering ingredients by assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name='Ingredient 1')
        Ingredient.objects.create(user=self.user, name='Ingredient 2')

        recipe1 = Recipe.objects.create(title='Recipe 1', time_minutes=10, user=self.user,price=Decimal('4.8'))
        recipe2 = Recipe.objects.create(title='Recipe 2', time_minutes=10, user=self.user,price=Decimal('4.8'))
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)
        res = self.client.get(INGREDIENTS_URL,{'assigned_only':1})
        self.assertEqual(len(res.data),1)
