"""
Views for recipe APIs
"""

from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)
from recipe import serializers

class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes in the database."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retrieve the authenticated user's recipes"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create new recipe"""
        serializer.save(user=self.request.user)

class BaseRecipeAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet):
    """Base Viewset for managing a model with attributes"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Filter querysets by authenicated user"""
        return self.queryset.filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseRecipeAttrViewSet):
    """Manage tags in the database"""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()

class IngredientViewSet(BaseRecipeAttrViewSet):
    """Manage ingredients in the database"""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
