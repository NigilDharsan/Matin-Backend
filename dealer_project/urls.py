from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from core.api import router as core_router

api = NinjaAPI(title="Dealer API", version="1.0")
api.add_router("/core/", core_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
