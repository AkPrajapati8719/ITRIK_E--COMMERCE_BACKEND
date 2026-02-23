from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import Blog, ContactMessage, SiteSettings
from .serializers import BlogSerializer, ContactMessageSerializer, SiteSettingsSerializer

logger = logging.getLogger(__name__)


class BlogViewSet(viewsets.ModelViewSet):
    serializer_class = BlogSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        # ✅ ONLY published blogs for public
        if self.request.user.is_staff:
            return Blog.objects.all()
        return Blog.objects.filter(published=True)

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]


@method_decorator(csrf_exempt, name='dispatch')
class ContactViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            contact = serializer.save()

            # optional email
            try:
                send_mail(
                    f"New Contact Message from {contact.name}",
                    f"Mobile: {contact.mobile}\n\n{contact.message}",
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True,
                )
            except Exception:
                pass

            return Response(
                {
                    "success": True,
                    "message": "Message received successfully"
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SiteSettingsViewSet(viewsets.ModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer

    def get_permissions(self):
        # ✅ frontend can READ, admin can WRITE
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]