from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from store.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer

logger = logging.getLogger(__name__)

# =====================================================
# 🖼️ IMAGE HELPER
# =====================================================

def get_product_image(product):
    try:
        if product.main_image:
            return product.main_image.url
        first = product.images.first()
        if first:
            return first.image.url
    except Exception:
        pass
    return ""


# =====================================================
# 🔄 MERGE GUEST CART (SAFE VERSION)
# =====================================================

def merge_session_cart_into_user(request, user_cart):
    session_cart = request.session.get("cart", {})

    if not session_cart:
        return

    for str_product_id, item_data in session_cart.items():
        try:
            qty = 1
            if isinstance(item_data, int):
                qty = item_data
            elif isinstance(item_data, dict):
                qty = item_data.get('quantity', 1)
            
            qty = int(qty)
            if qty <= 0: continue

            product = Product.objects.filter(id=str_product_id).first()
            if not product:
                continue

            item, created = CartItem.objects.get_or_create(
                cart=user_cart,
                product=product
            )

            if created:
                item.quantity = qty
            else:
                item.quantity += qty

            item.save()

        except Exception as e:
            logger.error(f"Error merging item {str_product_id}: {e}")
            continue

    request.session["cart"] = {}
    request.session.modified = True


# =====================================================
# 🛒 BUILD GUEST CART RESPONSE
# =====================================================

def build_guest_cart(session_cart):
    items = []
    total_price = 0
    total_items = 0

    if not isinstance(session_cart, dict):
        return {"items": [], "total_price": 0, "total_items": 0}

    for str_product_id, item_data in session_cart.items():
        try:
            qty = 1
            if isinstance(item_data, int):
                qty = item_data
            elif isinstance(item_data, dict):
                qty = item_data.get('quantity', 1)
            
            qty = int(qty)
            if qty <= 0: continue

            product = Product.objects.filter(id=str_product_id).first()
            if not product:
                continue

            price = float(product.discount_price or product.price)
            subtotal = price * qty

            items.append({
                "product": {
                    "id": str(product.id),
                    "slug": product.slug,
                    "title": product.title,
                    "image": get_product_image(product),
                    "price": price
                },
                "quantity": qty,
                "subtotal": subtotal
            })

            total_price += subtotal
            total_items += qty

        except Exception as e:
            continue

    return {
        "items": items,
        "total_price": total_price,
        "total_items": total_items
    }


# =====================================================
# 📥 GET CART
# =====================================================

class CartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
                
                if request.session.get("cart"):
                    merge_session_cart_into_user(request, cart)
                
                # 🔥 FIX: Pass 'request' context to Serializer
                return Response(CartSerializer(cart, context={'request': request}).data)

            session_cart = request.session.get("cart", {})
            return Response(build_guest_cart(session_cart))
            
        except Exception as e:
            logger.error(f"Cart Get Error: {e}")
            return Response({"items": [], "total_price": 0, "total_items": 0})


# =====================================================
# ➕ ADD TO CART
# =====================================================

class AddToCartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            product_id = request.data.get("product_id")
            quantity = int(request.data.get("quantity", 1))

            if not product_id:
                return Response({"error": "Product ID required"}, status=400)

            product = get_object_or_404(Product, id=product_id)

            if product.stock < quantity:
                return Response({"error": "Out of stock"}, status=400)

            # A. Logged In
            if request.user.is_authenticated:
                cart, _ = Cart.objects.get_or_create(user=request.user)
                
                if request.session.get("cart"):
                    merge_session_cart_into_user(request, cart)

                item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                
                if created:
                    item.quantity = quantity
                else:
                    item.quantity += quantity
                
                item.save()
                
                # 🔥 FIX: Pass 'request' context to Serializer
                return Response(CartSerializer(cart, context={'request': request}).data)

            # B. Guest
            cart = request.session.get("cart", {})
            
            current_qty = 0
            if str(product_id) in cart:
                val = cart[str(product_id)]
                if isinstance(val, int):
                    current_qty = val
                elif isinstance(val, dict):
                    current_qty = val.get('quantity', 0)

            cart[str(product_id)] = current_qty + quantity
            
            request.session["cart"] = cart
            request.session.modified = True

            return Response(build_guest_cart(cart))

        except Exception as e:
            logger.error(f"Add Cart Error: {e}")
            return Response({"error": "Server Error"}, status=500)


# =====================================================
# 🔄 UPDATE QUANTITY
# =====================================================

class UpdateCartItemView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        quantity = int(request.data.get("quantity", 1))

        if quantity < 1:
            return Response({"error": "Invalid quantity"}, status=400)

        if request.user.is_authenticated:
            cart = get_object_or_404(Cart, user=request.user)
            item = get_object_or_404(CartItem, id=item_id, cart=cart)

            if item.product.stock < quantity:
                return Response({"error": "Stock limit reached"}, status=400)

            item.quantity = quantity
            item.save()

            # 🔥 FIX: Pass 'request' context to Serializer
            return Response(CartSerializer(cart, context={'request': request}).data)

        return Response({"error": "Guest update not supported"}, status=400)


# =====================================================
# 🗑️ REMOVE ITEM
# =====================================================

class RemoveFromCartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        product_id = request.data.get("product_id")

        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                CartItem.objects.filter(cart=cart, product_id=product_id).delete()
                # 🔥 FIX: Pass 'request' context to Serializer
                return Response(CartSerializer(cart, context={'request': request}).data)

        cart = request.session.get("cart", {})
        cart.pop(str(product_id), None)
        request.session["cart"] = cart
        request.session.modified = True

        return Response(build_guest_cart(cart))


# =====================================================
# 🧹 CLEAR CART
# =====================================================

class ClearCartView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart.items.all().delete()
                # 🔥 FIX: Pass 'request' context to Serializer
                return Response(CartSerializer(cart, context={'request': request}).data)

        request.session["cart"] = {}
        request.session.modified = True

        return Response(build_guest_cart({}))