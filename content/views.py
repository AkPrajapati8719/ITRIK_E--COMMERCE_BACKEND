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
        # 1. Validate the incoming data
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # 2. SAVE to Database (This makes it appear in Django Admin)
            contact = serializer.save()

            # 3. Optional Email Notification logic
            try:
                send_mail(
                    subject=f"New Contact Message from {contact.name}",
                    message=f"Name: {contact.name}\nMobile: {contact.mobile}\n\nMessage:\n{contact.message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False, # Changed to False so errors show in your Render logs
                )
            except Exception as e:
                # Log the error to your console/Render logs but don't stop the 'success' response
                print(f"Admin Email Error: {e}") 
                pass

            # 4. Return success response to Frontend
            return Response(
                {
                    "success": True,
                    "message": "Message received successfully"
                },
                status=status.HTTP_201_CREATED
            )

        # If data is invalid (e.g. mobile number format error), return 400
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SiteSettingsViewSet(viewsets.ModelViewSet):
    queryset = SiteSettings.objects.all()
    serializer_class = SiteSettingsSerializer

    def get_permissions(self):
        # ✅ frontend can READ, admin can WRITE
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        return [AllowAny()]