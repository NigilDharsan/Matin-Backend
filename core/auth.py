from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.conf import settings
from typing import Optional

User = get_user_model()

def get_auth_class():
    """Returns the appropriate auth class based on settings"""
    if settings.API_AUTHENTICATION_ENABLED:
        print("Authentication is ENABLED, using JWTAuth")
        return JWTAuth
    else:
        print("Authentication is DISABLED, using NoAuth")
        return None  # Return None to disable authentication completely

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        if not token:
            return None

        try:
            validated = AccessToken(token)
            user_id = validated['user_id']
            request.user = User.objects.get(id=user_id)
            return True
        except Exception as e:
            print(f"Authentication error: {str(e)}")  # For debugging
            return None
