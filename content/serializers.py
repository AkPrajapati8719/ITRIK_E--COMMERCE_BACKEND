from rest_framework import serializers
from .models import Blog, ContactMessage, SiteSettings


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = [
            'id',
            'title',
            'slug',
            'category',        # ✅ added (required)
            'content',
            'excerpt',
            'image',           # ✅ renamed (was featured_image)
            'author',
            'published',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            'id',
            'site_name',
            'hero_title',
            'hero_subtitle',
            'hero_image',
            'hero_button_text',
            'about_text',
            'contact_email',
            'contact_phone',
            'address',
            'instagram_url',
            'facebook_url',
            'twitter_url',
            'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']