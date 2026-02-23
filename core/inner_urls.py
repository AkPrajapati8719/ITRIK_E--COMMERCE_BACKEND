from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogViewSet, ContactViewSet, SiteSettingsViewSet

router = DefaultRouter()
router.register(r'blog', BlogViewSet, basename='blog')
router.register(r'contact', ContactViewSet, basename='contact')
router.register(r'settings', SiteSettingsViewSet, basename='settings')

urlpatterns = [
    path('', include(router.urls)),
]
