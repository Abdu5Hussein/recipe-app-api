""" test recipe api's """
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Recipe,Tag
from django.test import TestCase
from decimal import Decimal
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)

RECIPE_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """ create and return a recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def create_recipe(user,**params):
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.99'),
        'description': 'Sample recipe description',
        'link': 'https://example.com/recipe',
        }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    """create and return a new user"""
    return get_user_model().objects.create_user(**params)

class PublicRecipeAPITests(TestCase):
    """test un-auth api requests"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test that authentication is required"""
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    """test authenticated api requests"""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com",password='password123')

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """test retrieving a list of recipes"""
        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """test retrieving recipes for user"""
        other_user = create_user(email="other@example.com",password='password123')
        create_recipe(user=other_user)
        create_recipe(self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """test retrieving a recipe's detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)
        serializer = RecipeSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """test creating a new recipe"""
        payload = {
            'title': 'Test recipe',
            'time_minutes': 30,
            'price': Decimal('10.99'),
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """test updating a recipe with a patch request"""
        original_link = 'https//example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title= 'sample title',
            link=original_link
        )
        payload = {
            'title': 'New title',
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.link, original_link)
    def test_full_update(self):
        """test updating a recipe with a put request"""
        recipe = create_recipe(
            user=self.user,
            title= 'old title',
            link='https://example.com/recipe.pdf',
            description='old desc'
            )
        payload = {
            'title': 'New title',
            'time_minutes': 20,
            'price': Decimal('5.99'),
            'link': 'https://example.com/new_recipe.pdf',
            'description': 'New desc',
            }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(value, getattr(recipe, key))
        self.assertEqual(recipe.user,self.user)

    def test_update_user_return_error(self):
        """test updating the user associated with a recipe returns an error"""
        new_user = create_user(email='newuser@example.com',password='newpass')
        recipe = create_recipe(user=self.user, title='sample title')
        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """test Deleting a recipe """
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipes_error(self):
        """ test deleting other users recipes """
        new_user = create_user(email='newuser@example.com',password='newpass')
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """test creating a new recipe with new tags"""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': Decimal('5.99'),
            'tags':[{'name':'Thai'},{'name':'libyan'}]
        }

        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """test creating a new recipe with existing tags"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Sample recipe',
            'time_minutes':40,
            'price': Decimal('5.99'),
            'tags':[{'name':'Indian'}, {'name':'Libyan'}]
        }
        res = self.client.post(RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian,recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], user=self.user
                ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """test creating a tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {'tags':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user,name='Lunch')
        self.assertIn(new_tag,recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """test updating a recipe with a new tag"""
        recipe = create_recipe(user=self.user)
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')

        recipe.tags.add(tag_breakfast)
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {
            'tags':[{'name':'Lunch'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch,recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all(),)

    def test_clear_recipe_tags(self):
        """test clearing a recipe's tags"""
        recipe = create_recipe(user=self.user)
        tag1 = Tag.objects.create(user=self.user, name='Tag1')
        recipe.tags.add(tag1)
        payload = {
            'tags': []
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)