""" test tags api's """
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Tag
from django.test import TestCase
# from decimal import Decimal
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def detail_url(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])

def create_user(email='user@example.com',password='testpass123'):
    """create and return user """
    return get_user_model().objects.create_user(email=email,password=password)

class PublicTagsApiTests(TestCase):
    """test unauthenticated api requests """
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """test that authentication is required """
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTests(TestCase):
    """test authenticated api requests """
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """test retrieving a list of tags """
        Tag.objects.create(name='tag1',user=self.user)
        Tag.objects.create(name='tag2',user=self.user)
        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags,many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)
    def test_tags_limited_to_user(self):
        """test that tags returned are for the authenticated user """
        user2 = create_user(email='user2@example.com',password='testpass123')
        tag = Tag.objects.create(name='tag1',user=user2)
        tag2 = Tag.objects.create(name='tag2',user=self.user)
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'],tag2.name)
        self.assertEqual(res.data[0]['id'],tag2.id)

    def test_update_tag(self):
        """test updating a tag """
        old_name = 'old name'
        tag = Tag.objects.create(user=self.user,name=old_name)
        url = detail_url(tag.id)
        data = {'name':'new name'}
        res = self.client.patch(url,data)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name,'new name')

    def test_delete_tag(self):
        """test deleting a tag """
        tag = Tag.objects.create(user=self.user,name='tag1')
        url = detail_url(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code,status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())