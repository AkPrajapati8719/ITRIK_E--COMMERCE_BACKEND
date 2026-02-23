from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode


# =====================================================
# 👤 USER ADMIN
# =====================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        "email",
        "full_name",
        "mobile_number",
        "is_delivery_partner",
        "is_verified",
        "profile_completed",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_delivery_partner",
        "is_verified",
        "is_active",
        "created_at",
    )

    search_fields = ("email", "mobile_number", "full_name")
    ordering = ("email",)
    readonly_fields = ("id", "created_at")

    fieldsets = (
        (None, {
            "fields": ("id", "email", "password")
        }),

        ("Personal Info", {
            "fields": ("full_name", "mobile_number", "alternate_mobile")
        }),

        ("Address", {
            "fields": ("shipping_address", "delivery_pincode")
        }),

        ("Roles & Status", {
            "fields": (
                "is_delivery_partner",
                "is_verified",
                "profile_completed",
                "is_active",
                "is_staff",
                "is_superuser",
            )
        }),

        ("Permissions", {
            "fields": ("groups", "user_permissions")
        }),

        ("System", {
            "fields": ("created_at",)
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "password1",
                "password2",
                "is_delivery_partner",
                "is_staff",
                "is_superuser",
            )
        }),
    )

    filter_horizontal = ("groups", "user_permissions")


# =====================================================
# 🔐 OTP ADMIN
# =====================================================

@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):

    list_display = ("identifier", "code", "attempts", "created_at")
    list_filter = ("created_at",)
    search_fields = ("identifier", "code")
    readonly_fields = ("identifier", "created_at")
