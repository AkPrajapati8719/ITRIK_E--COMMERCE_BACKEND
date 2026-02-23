from django.contrib import admin
from .models import Cart, CartItem


# =====================================================
# CART ITEM INLINE
# =====================================================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("id", "added_at", "updated_at")
    autocomplete_fields = ["product"]
    show_change_link = True


# =====================================================
# CART ADMIN
# =====================================================

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "session_key",
        "get_total_items",
        "get_total_price",
        "updated_at",
    )

    list_filter = ("updated_at",)
    search_fields = ("user__email", "user__full_name", "session_key")

    inlines = [CartItemInline]

    readonly_fields = ("id", "created_at", "updated_at", "session_key")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items", "items__product")

    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = "Total Items"

    def get_total_price(self, obj):
        return f"₹{obj.get_total_price()}"
    get_total_price.short_description = "Total Price"


# =====================================================
# CART ITEM ADMIN
# =====================================================

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "cart",
        "quantity",
        "get_subtotal",
        "added_at",
    )

    list_filter = ("added_at",)
    search_fields = ("product__title", "cart__user__email", "cart__session_key")

    readonly_fields = ("id", "added_at", "updated_at")

    autocomplete_fields = ["product", "cart"]

    def get_subtotal(self, obj):
        return f"₹{obj.get_subtotal()}"
    get_subtotal.short_description = "Subtotal"
