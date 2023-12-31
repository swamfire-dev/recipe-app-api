"""
Test for Tags API
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

from decimal import Decimal
from core.models import (
    Tag,
    Recipe,
)

TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Return url for specific tag id."""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="test@example.com", password="testpass123"):
    """Create a new user with email and passowrd."""
    return get_user_model().objects.create_user(email=email, password=password)



class PublicTagsApiTests(TestCase):
    """Test unauthenticated API requests."""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTests(TestCase):
    """Test authenticated tag api request."""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieve all the tags in db by authorized user"""
        # Create two tags to be retrieved from database
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')
        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that only users can view their own tags"""
        other_user = create_user('user2@example.com')
        # Create three tags as different users
        Tag.objects.create(user=other_user, name='Fruity')
        # Test that we cannot see this tag because it's not ours!
        tag = Tag.objects.create(user=self.user, name='Sweet')
        res = self.client.get(TAGS_URL)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tags(self):
        """Test updating of tags"""
        # Update an existing tag
        tag = Tag.objects.create(user = self.user, name="After Dinner")
        payload = {"name": "Before Lunch"}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tags(self):
        """Test deleting a single tag"""
        tag = Tag.objects.create(user=self.user, name="Breakfast")
        url = detail_url(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Filter tags assigned to recipes"""
        recipe1 = Recipe.objects.create(
            title="Eggs",
            time_minutes=5,
            price=3.99,
            user=self.user,
        )
        tag1 = Tag.objects.create(user = self.user, name="Breakfast")
        recipe1.tags.add(tag1)
        tag2 = Tag.objects.create(user =self.user, name="Lunch")

        res = self.client.get(TAGS_URL, {'assigned_only':1})
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filtered_tags_unique(self):
        """Filtering tags by assigned returns unique items only."""
        tag = Tag.objects.create(user=self.user, name="Breakfast")
        Tag.objects.create(user=self.user, name="Dinner")
        recipe1 = Recipe.objects.create(
            title='Pancakes',
            time_minutes=60,
            price=7.89,
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title="Porridge",
            time_minutes=10,
            price=1.99,
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2.tags.add(tag)
        res = self.client.get(TAGS_URL, {"assigned_only": 1})
        self.assertEqual(len(res.data), 1)
