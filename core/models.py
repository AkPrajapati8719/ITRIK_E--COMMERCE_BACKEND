from django.db import models
import uuid


class Blog(models.Model):
    """Blog posts for content management."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=500, blank=True)
    featured_image = models.ImageField(upload_to='blog/images/')
    author = models.CharField(max_length=100, default='ITRIK Team')
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """Contact form submissions."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.name} - {self.subject}'


class SiteSettings(models.Model):
    """Site-wide settings for admin panel."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    site_name = models.CharField(max_length=100, default='ITRIK')
    hero_title = models.CharField(max_length=255, default='Welcome to ITRIK')
    hero_subtitle = models.TextField(default='Premium earthy aesthetics for the modern professional')
    hero_image = models.ImageField(upload_to='site/hero/')
    hero_button_text = models.CharField(max_length=50, default='Shop Now')
    
    about_text = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
