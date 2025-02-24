from django.shortcuts import render
from rest_framework import generics, authentication, permissions
from user.serializers import (
    UserSerializer,
    authTokenSerializer
    )

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

# Create your views here.

class CreateUserView(generics.CreateAPIView):
    """create a new user in the system"""
    serializer_class = UserSerializer

class CreateTokenView(ObtainAuthToken):
    """create a token for user"""
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = authTokenSerializer

class ManageUserView(generics.RetrieveUpdateAPIView):
    """manage the authenticated user"""
    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        """retrieve and return authenticated user"""
        return self.request.user