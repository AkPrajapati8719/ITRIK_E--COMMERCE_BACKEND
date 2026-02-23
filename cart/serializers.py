from rest_framework import serializers
from .models import Cart, CartItem
from store.models import Product
from store.serializers import ProductListSerializer


# =====================================================
# CART ITEM
# =====================================================

class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual cart items.
    """

    product = ProductListSerializer(read_only=True)

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source="product"
    )

    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "subtotal",
            "added_at",
        ]
        read_only_fields = ["id", "added_at"]

    def get_subtotal(self, obj):
        return float(obj.get_subtotal())

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


# =====================================================
# CART
# =====================================================

class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for full cart (guest + user).
    """

    items = CartItemSerializer(many=True, read_only=True)

    total_price = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()

    # Expose ownership (useful for debugging + merge)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    session_key = serializers.CharField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "session_key",
            "items",
            "total_price",
            "total_items",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at", "user", "session_key"]

    def get_total_price(self, obj):
        return float(obj.get_total_price())

    def get_total_items(self, obj):
        return int(obj.get_total_items())
