from django.contrib import admin, messages
from .models import Blog, ContactMessage, SiteSettings


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "published", "created_at")
    list_filter = ("published", "category", "created_at")
    search_fields = ("title", "content", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": ("title", "slug", "category", "author", "published")
        }),
        ("Content", {
            "fields": ("excerpt", "content")
        }),
        ("Media", {
            "fields": ("image",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    def has_add_permission(self, request):
        """
        Block Add button after 3 blogs.
        Show message ONLY on Add Blog page.
        """
        count = Blog.objects.count()

        if count >= 15:
            if request.path.endswith("/add/"):
                self.message_user(
                    request,
                    "Only 15 Blogs are accepted. You can update them.",
                    level=messages.ERROR
                )
            return False

        return True

    # JS loaded ONLY for Blog admin (not whole admin)
    class Media:
        js = ("admin/js/auto_hide_messages.js",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "mobile", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "mobile", "message")
    readonly_fields = ("id", "name", "mobile", "message", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "contact_email", "updated_at")
    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Branding", {
            "fields": ("site_name",)
        }),
        ("Hero Section", {
            "fields": ("hero_title", "hero_subtitle", "hero_image", "hero_button_text")
        }),
        ("About & Contact", {
            "fields": ("about_text", "contact_email", "contact_phone", "address")
        }),
        ("Social Links", {
            "fields": ("instagram_url", "facebook_url", "twitter_url")
        }),
    )