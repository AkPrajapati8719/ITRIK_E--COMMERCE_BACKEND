from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from .models import Order, OrderItem, OrderStatusHistory
from cart.models import CartItem
import random
import hashlib

# =====================================================
# ORDER ITEMS INLINE
# =====================================================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "id",
        "product",
        "quantity",
        "price_at_purchase",
    )
    can_delete = False


# =====================================================
# STATUS TIMELINE INLINE
# =====================================================

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = (
        "id",
        "status",
        "changed_at",
        "notes",
    )
    can_delete = False


# =====================================================
# ORDER ADMIN (ENTERPRISE CONTROL PANEL)
# =====================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "status",
        "delivery_agent", # 🔥 NEW: See assigned agent
        "payment_method",
        "payment_status",
        "is_paid",
        "total_amount_display",
        "estimated_delivery_date",
        "created_at",
    )

    list_editable = (
        "status",
        "payment_status",
        "delivery_agent", # 🔥 NEW: Quickly assign an agent from the list
    )

    list_filter = (
        "status",
        "payment_method",
        "payment_status",
        "is_paid",
        "is_cancelled", # 🔥 NEW: Filter by failed deliveries
        "created_at",
    )

    search_fields = (
        "id",
        "user__email",
        "user__full_name",
        "user__mobile_number",
        "delivery_pincode",
        "delivery_agent__email", # 🔥 NEW: Search by agent
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "cancel_allowed_until",
        "delivery_otp_hash",
        "refund_amount",
        "delivered_at", # 🔥 NEW: Read-only timestamp
    )

    inlines = [
        OrderItemInline,
        OrderStatusHistoryInline,
    ]

    fieldsets = (
        ("Order Info", {
            "fields": (
                "id",
                "user",
                "status",
            )
        }),

        ("Payment Lifecycle", {
            "fields": (
                "payment_method",
                "payment_status",
                "is_paid",
                "razorpay_order_id",
                "razorpay_payment_id",
                "refund_amount",
            )
        }),

        ("Pricing Breakdown", {
            "fields": (
                "items_total",
                "shipping_cost",
                "total_amount",
            )
        }),

        ("Delivery Details", {
            "fields": (
                "shipping_address_snapshot",
                "delivery_pincode",
                "eta_days",
                "estimated_delivery_date",
            )
        }),

        ("Agent & Logistics Tracking", { # 🔥 NEW FIELDSET
            "fields": (
                "delivery_agent",
                "delivery_otp_hash",
                "otp_verified",
                "delivered_at",
                "is_cancelled",
                "cancel_reason",
            )
        }),

        ("System Controls", {
            "fields": (
                "cancel_allowed_until",
                "created_at",
                "updated_at",
            )
        }),
    )

    ordering = ("-created_at",)

    # =================================================
    # CUSTOM ACTIONS (AMAZON FLOW)
    # =================================================
    
    actions = ["send_delivery_otp", "force_clear_user_cart"]

    @admin.action(description="📲 Generate & Log Delivery OTP (Manual Override)")
    def send_delivery_otp(self, request, queryset):
        for order in queryset:
            if order.status not in ["shipped", "out_for_delivery"]:
                order.status = "out_for_delivery"
            
            otp = str(random.randint(100000, 999999))
            order.delivery_otp_hash = hashlib.sha256(otp.encode()).hexdigest()
            order.save()
            
            OrderStatusHistory.objects.create(
                order=order,
                status=order.status,
                notes=f"Admin generated OTP: {otp}"
            )
            
            self.message_user(
                request, 
                f"OTP for Order #{str(order.id)[:8]} generated successfully.", 
                messages.SUCCESS
            )

    @admin.action(description="🛒 Force Clear User's Active Cart")
    def force_clear_user_cart(self, request, queryset):
        for order in queryset:
            CartItem.objects.filter(cart__user=order.user).delete()
        self.message_user(request, "Selected users' carts have been cleared.", messages.WARNING)

    # =================================================
    # CURRENCY FORMATTING
    # =================================================

    def items_total_display(self, obj):
        return f"₹{obj.items_total:.2f}"

    def shipping_cost_display(self, obj):
        return f"₹{obj.shipping_cost:.2f}"

    def total_amount_display(self, obj):
        return f"₹{obj.total_amount:.2f}"

    items_total_display.short_description = "Items Total"
    shipping_cost_display.short_description = "Shipping"
    total_amount_display.short_description = "Final Amount"


# =====================================================
# ORDER ITEM ADMIN
# =====================================================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "order",
        "quantity",
        "price_at_purchase",
        "subtotal_display",
    )

    list_filter = (
        "order__created_at",
    )

    search_fields = (
        "product__title",
        "order__id",
    )

    readonly_fields = (
        "id",
        "price_at_purchase",
    )

    def subtotal_display(self, obj):
        return f"₹{obj.subtotal():.2f}"

    subtotal_display.short_description = "Subtotal"


# =====================================================
# STATUS HISTORY ADMIN
# =====================================================

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "status",
        "changed_at",
        "notes",
    )

    list_filter = (
        "status",
        "changed_at",
    )

    search_fields = (
        "order__id",
        "status",
    )

    readonly_fields = (
        "id",
        "changed_at",
    )

    ordering = ("-changed_at",)