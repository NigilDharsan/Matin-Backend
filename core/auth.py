from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
User=get_user_model()
class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            validated=AccessToken(token)
            user_id=validated['user_id']
            request.user=User.objects.get(id=user_id)
            return request.user
        except Exception:
            return AnonymousUser()
