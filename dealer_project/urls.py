from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from core.api import router as core_router, auth_router as core_auth_router

api = NinjaAPI(title="Dealer API", version="1.0")
api.add_router("/core/", core_router)
api.add_router("/auth/", core_auth_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
