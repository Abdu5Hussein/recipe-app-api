from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models
from unittest.mock import patch

def create_user(email='user@example.com',password='testpass123'):
    """ create and return new user"""
    return get_user_model().objects.create_user(email,password)

class ModelTests(TestCase):
    """test models"""

    def test_create_user_with_email_successful(self):
        """test creating a new user with an email is successful"""
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """test the email for a new user is normalized"""
        sample_emails = [
            ['test1@example.Com','test1@example.com'],
            ['TEST2@EXAMPLE.COM','TEST2@example.com'],
            ['Test3@Example.COM','Test3@example.com'],
            ['TeST4@Example.com','TeST4@example.com'],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'test123')
            self.assertEqual(user.email, expected)


    def test_create_new_user_without_email(self):
        """test without email user creation"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('','test123')

    def test_create_superuser(self):
        """test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_tag(self):
        """test creating a new tag"""
        tag = models.Tag.objects.create(
            user=create_user(),
            name='test tag',
            )
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        """test creating a new ingredient"""
        ingredient = models.Ingredient.objects.create(
            user=create_user(),
            name='test ingredient',
            )
        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test genetaing image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None,'example.jpg')

        self.assertEqual(file_path,f'uploads/recipe/{uuid}.jpg')