from django.contrib import admin
from .models import (
    Category,
    Product,
    Review,
    ProductImage,
    ProductFeature
)


# =========================
# 📸 PRODUCT IMAGES INLINE (1–6)
# =========================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    min_num = 1
    max_num = 6
    verbose_name = "Product Image"
    verbose_name_plural = "Product Images"


# =========================
# ✔ PRODUCT FEATURES INLINE (1–15)
# =========================

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
    min_num = 1
    max_num = 15
    verbose_name = "Feature Point"
    verbose_name_plural = "Feature Points"


# =========================
# PRODUCT ADMIN
# =========================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "category",
        "price",
        "discount_price",
        "stock",
        "is_featured",
        "created_at",
    )

    list_filter = ("category", "is_featured", "created_at")
    search_fields = ("title", "slug")

    prepopulated_fields = {"slug": ("title",)}

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {
            "fields": ("id", "title", "slug", "category")
        }),
        ("Description", {
            "fields": ("description",)
        }),
        ("Pricing", {
            "fields": ("price", "discount_price")
        }),
        ("Stock & Featured", {
            "fields": ("stock", "is_featured")
        }),
        ("Media", {
            "fields": ("main_image", "video_file")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at")
        }),
    )

    # 🔥 BOTH images + feature points inline
    inlines = [ProductImageInline, ProductFeatureInline]


# =========================
# CATEGORY ADMIN
# =========================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


# =========================
# REVIEW ADMIN
# =========================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__full_name", "product__title")
    readonly_fields = ("id", "created_at", "updated_at")