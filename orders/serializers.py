from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from store.serializers import ProductListSerializer


# =====================================================
# ORDER ITEM
# =====================================================

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "price_at_purchase",
            "subtotal",
        ]

    def get_subtotal(self, obj):
        return obj.subtotal()


# =====================================================
# STATUS HISTORY (TIMELINE)
# =====================================================

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    # 🔥 ADDED: Human-readable status (e.g., "Out for Delivery")
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            "status",
            "status_display",
            "changed_at",
            "notes",
        ]


# =====================================================
# ORDER LIST (DASHBOARD VIEW)  ✅ ENHANCED
# =====================================================

class OrderListSerializer(serializers.ModelSerializer):
    # 🔥 ADDED: Full product items for dashboard preview
    items = OrderItemSerializer(many=True, read_only=True)
    
    # 🔥 ADDED: Human-readable status
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    items_count = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "status_display",  # NEW
            "payment_method",
            "payment_status",
            "items_total",
            "shipping_cost",
            "total_amount",
            "estimated_delivery_date",

            # 🔥 NEW (no removals)
            "items",

            "items_count",
            "can_cancel",
            "created_at",
        ]

    def get_items_count(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_can_cancel(self, obj):
        return obj.can_cancel()


# =====================================================
# FULL ORDER DETAILS (TRACKING / ORDER PAGE)
# =====================================================

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    # 🔥 ADDED: Human-readable status
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "status_display", # NEW
            "payment_method",
            "payment_status",
            "is_paid",
            "items_total",
            "shipping_cost",
            "total_amount",
            "shipping_address_snapshot",
            "delivery_pincode",
            "estimated_delivery_date",
            
            # 🔥 NEW: Delivery tracking fields
            "delivered_at",
            "is_cancelled",
            "cancel_reason",

            "items",
            "status_history",
            "can_cancel",
            "created_at",
        ]

    def get_can_cancel(self, obj):
        return obj.can_cancel()


# =====================================================
# ORDER CREATION INPUT (CHECKOUT)
# =====================================================

class CreateOrderSerializer(serializers.Serializer):
    """
    Handles:
    - Direct Buy
    - Cart Checkout
    - COD / Prepaid selection
    """

    type = serializers.ChoiceField(
        choices=["direct", "cart"]
    )

    payment_method = serializers.ChoiceField(
        choices=["cod", "prepaid"],
        default="cod"
    )

    product_id = serializers.UUIDField(
        required=False
    )

    quantity = serializers.IntegerField(
        default=1,
        min_value=1
    )

    def validate(self, data):

        order_type = data["type"]

        # ✅ Direct buy must have product
        if order_type == "direct" and not data.get("product_id"):
            raise serializers.ValidationError(
                "product_id required for direct order"
            )

        # ✅ Cart checkout must NOT send product_id
        if order_type == "cart" and data.get("product_id"):
            raise serializers.ValidationError(
                "product_id not allowed for cart checkout"
            )

        return data