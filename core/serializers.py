from rest_framework import serializers
from core.models import Blog, ContactMessage, SiteSettings


class BlogSerializer(serializers.ModelSerializer):
    """Serializer for blog posts."""
    
    class Meta:
        model = Blog
        fields = ['id', 'title', 'slug', 'excerpt', 'content', 'featured_image', 
                  'author', 'published', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer for contact messages."""
    
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'message', 'phone', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class SiteSettingsSerializer(serializers.ModelSerializer):
    """Serializer for site settings."""
    
    class Meta:
        model = SiteSettings
        fields = ['id', 'site_name', 'hero_title', 'hero_subtitle', 'hero_image',
                  'hero_button_text', 'about_text', 'contact_email', 'contact_phone',
                  'address', 'instagram_url', 'facebook_url', 'twitter_url', 'updated_at']
        read_only_fields = ['id', 'updated_at']
