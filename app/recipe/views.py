""" views for recipe api's """

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets,mixins

from core.models import Recipe,Tag
from recipe import serializers

class RecipeViewSet(viewsets.ModelViewSet):
    """Manage recipes API's"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()

    def get_queryset(self):
        """Retrieve the recipes for the authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self,serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)  # save the recipe with the authenticated user


class TagViewSet(
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
    ):
    """Manage tags API's"""
    authentication_classes = [TokenAuthentication]
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()  # get all tags from the database
    permission_classes = [IsAuthenticated]  # only authenticated users can access this view

    def get_queryset(self):
        """Retrieve the tags for the authenticated user"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

