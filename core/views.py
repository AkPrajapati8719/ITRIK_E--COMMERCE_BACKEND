from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from core.models import Blog, ContactMessage, SiteSettings
from core.serializers import BlogSerializer, ContactMessageSerializer, SiteSettingsSerializer


class BlogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog posts.
    List: GET /api/blog/
    Create: POST /api/blog/ (admin only)
    Retrieve: GET /api/blog/{id}/
    Update: PUT /api/blog/{id}/ (admin only)
    Delete: DELETE /api/blog/{id}/ (admin only)
    """
    
    queryset = Blog.objects.filter(published=True)
    serializer_class = BlogSerializer
    lookup_field = 'slug'
    
    def get_permissions(self):
        """Allow read for everyone, write for admin only."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def create(self, request, *args, **kwargs):
        """Create blog post (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'success': False, 'message': 'Only admins can create blog posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Blog post created successfully',
            'blog': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update blog post (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'success': False, 'message': 'Only admins can update blog posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete blog post (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'success': False, 'message': 'Only admins can delete blog posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class ContactViewSet(viewsets.ViewSet):
    """
    ViewSet for contact messages.
    Create: POST /api/contact/
    List: GET /api/contact/ (admin only)
    Mark Read: POST /api/contact/{id}/mark-read/ (admin only)
    """
    
    def create(self, request):
        """Create contact message."""
        serializer = ContactMessageSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Thank you for your message. We will contact you soon!',
                'contact': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def list_messages(self, request):
        """List all contact messages (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'success': False, 'message': 'Only admins can view messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = ContactMessage.objects.all()
        serializer = ContactMessageSerializer(messages, many=True)
        return Response({
            'success': True,
            'count': messages.count(),
            'messages': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'success': False, 'message': 'Only admins can mark messages as read'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message = get_object_or_404(ContactMessage, id=pk)
        message.is_read = True
        message.save()
        
        serializer = ContactMessageSerializer(message)
        return Response({
            'success': True,
            'message': 'Message marked as read',
            'contact': serializer.data
        }, status=status.HTTP_200_OK)


class SiteSettingsViewSet(viewsets.ViewSet):
    """
    ViewSet for site settings.
    Get: GET /api/settings/
    Update: PUT /api/settings/ (admin only)
    """
    
    @action(detail=False, methods=['get'])
    def get_settings(self, request):
        """Get site settings."""
        try:
            settings = SiteSettings.objects.first()
            if not settings:
                # Create default settings
                settings = SiteSettings.objects.create()
            
            serializer = SiteSettingsSerializer(settings)
            return Response({
                'success': True,
                'settings': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['put'])
    def update_settings(self, request):
        """Update site settings (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'success': False, 'message': 'Only admins can update settings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        settings = SiteSettings.objects.first()
        if not settings:
            settings = SiteSettings.objects.create()
        
        serializer = SiteSettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Settings updated successfully',
                'settings': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
