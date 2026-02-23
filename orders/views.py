from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from decimal import Decimal
import random
import hashlib
from django.utils import timezone
from datetime import timedelta

# Utils
from orders.utils.sms import send_sms
from orders.utils.razorpay import (
    create_razorpay_order,
    verify_payment_signature,
    verify_webhook_signature,
    handle_webhook,
    refund_payment,
    mark_payment_success
)

# Models & Serializers
from .models import Order, OrderItem, OrderStatusHistory
from .serializers import (
    OrderDetailSerializer,
    OrderListSerializer,
    CreateOrderSerializer
)
from cart.models import Cart, CartItem  # Added CartItem import
from store.models import Product


# =====================================================
# 🚚 SHIPPING CONFIG
# =====================================================

FREE_SHIPPING_MIN = Decimal("999.00")
REMOTE_SURCHARGE = Decimal("120.00")

def calculate_shipping(pincode, items_total):
    pincode = int(pincode or 0)

    # Amazon-style slab system

    if 100000 <= pincode <= 199999:        # Same city / metro zone
        base, eta = Decimal("49"), 2

    elif 200000 <= pincode <= 299999:      # Nearby districts
        base, eta = Decimal("79"), 3

    elif 300000 <= pincode <= 399999:      # Same state
        base, eta = Decimal("99"), 4

    elif 400000 <= pincode <= 599999:      # Neighbor states
        base, eta = Decimal("129"), 5

    elif 600000 <= pincode <= 699999:      # Long distance
        base, eta = Decimal("159"), 6

    elif 700000 <= pincode <= 799999:      # Far zones
        base, eta = Decimal("189"), 7

    else:                                 # Extreme remote
        base, eta = Decimal("249"), 9

    # 🎁 Free shipping rule
    if items_total >= FREE_SHIPPING_MIN:
        base = Decimal("0")

    # 🚧 Remote logistics surcharge
    if pincode >= 700000:
        base += REMOTE_SURCHARGE

    return base, eta


# =====================================================
# 🔐 OTP ENGINE
# =====================================================

def generate_otp():
    return str(random.randint(100000, 999999))

def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()


# =====================================================
# 📦 ORDER LIST + DETAIL + CANCEL ACTION
# =====================================================

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related("items", "status_history").order_by('-created_at')

    def get_serializer_class(self):
        return OrderListSerializer if self.action == "list" else OrderDetailSerializer

    # 🔥 ADDED: Cancel Action (Required for Dashboard)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        # order = self.get_object()
        order = get_object_or_404(Order, id=pk)
        
        # Only allow cancel for specific statuses
        if order.status not in ['pending_payment', 'processing']:
            return Response({'message': 'Cannot cancel this order at this stage.'}, status=400)
        
        order.status = 'cancelled'
        order.save()
        
        # If paid online, initiate refund (Optional logic)
        # if order.payment_status == 'Paid': refund_payment(order)

        OrderStatusHistory.objects.create(
            order=order, 
            status='Cancelled', 
            notes="Cancelled by user from dashboard"
        )
        return Response({'status': 'Order cancelled'})


# =====================================================
# 🚚 SHIPPING PREVIEW
# =====================================================

class ShippingPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.shipping_address or not user.delivery_pincode:
            return Response({"message": "Add delivery address first"}, status=400)

        order_type = request.data.get("type")

        items_total = Decimal("0.00")

        # ===== DIRECT BUY =====
        if order_type == "direct":
            product_id = request.data.get("product_id")
            quantity = int(request.data.get("quantity", 1))

            if not product_id:
                return Response({"message": "Product required"}, status=400)

            product = get_object_or_404(Product, id=product_id)
            price = product.discount_price or product.price
            items_total = price * quantity

        # ===== CART BUY =====
        else:
            cart = Cart.objects.filter(user=user).first()
            if not cart or not cart.items.exists():
                return Response({"message": "Cart empty"}, status=400)

            for item in cart.items.all():
                price = item.product.discount_price or item.product.price
                items_total += price * item.quantity

        shipping_cost, eta_days = calculate_shipping(
            user.delivery_pincode,
            items_total
        )

        return Response({
            "items_total": items_total,
            "shipping_cost": shipping_cost,
            "final_total": items_total + shipping_cost,
            "eta_days": eta_days
        })


# =====================================================
# 🛒 CREATE ORDER (CORE LOGIC)
# =====================================================

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        payment_method = serializer.validated_data["payment_method"]
        order_type = serializer.validated_data["type"]

        if not user.shipping_address or not user.delivery_pincode:
            return Response({"message": "Please add your delivery address in the dashboard first."}, status=400)

        items_total = Decimal("0.00")
        locked_products = []

        # A. DIRECT BUY
        if order_type == "direct":
            product_id = request.data.get("product_id")
            if not product_id:
                return Response({"message": "Product ID required"}, status=400)

            product = Product.objects.select_for_update().get(id=product_id)
            quantity = serializer.validated_data.get("quantity", 1)

            if product.stock < quantity:
                return Response({"message": "Stock insufficient"}, status=400)

            price = product.discount_price or product.price
            items_total = price * quantity
            locked_products.append((product, quantity, price))

        # B. CART BUY
        else:
            cart = Cart.objects.select_for_update().filter(user=user).first()
            if not cart or not cart.items.exists():
                return Response({"message": "Cart is empty"}, status=400)

            for item in cart.items.select_related("product").select_for_update():
                product = item.product
                if product.stock < item.quantity:
                    return Response({"message": f"{product.title} out of stock"}, status=400)

                price = product.discount_price or product.price
                items_total += price * item.quantity
                locked_products.append((product, item.quantity, price))

        # CREATE ORDER
        shipping_cost, eta_days = calculate_shipping(user.delivery_pincode, items_total)
        final_total = items_total + shipping_cost
        
        status_value = "processing" if payment_method == "cod" else "pending_payment"

        order = Order.objects.create(
            user=user,
            status=status_value,
            payment_method=payment_method,
            payment_status="pending",
            items_total=items_total,
            shipping_cost=shipping_cost,
            total_amount=final_total,
            shipping_address_snapshot=user.shipping_address,
            delivery_pincode=user.delivery_pincode,
            eta_days=eta_days,
        )

        for product, qty, price in locked_products:
            OrderItem.objects.create(
                order=order, product=product, quantity=qty, price_at_purchase=price
            )
            product.stock -= qty
            product.save(update_fields=["stock"])

        # 🔥 CART CLEARING LOGIC (ROBUST)
        if order_type == "cart":
            # 1. Clear Database Items (Explicit)
            CartItem.objects.filter(cart__user=user).delete()
            
            # 2. Clear Session Cart (Backup)
            if 'cart' in request.session:
                request.session['cart'] = {}
                request.session.modified = True

        OrderStatusHistory.objects.create(
            order=order, status=status_value, notes=f"Order placed ({payment_method.upper()})"
        )

        response = {
            "order_id": order.id,
            "payment_method": payment_method,
            "final_total": final_total,
            "success": True
        }

        if payment_method == "prepaid":
            response["razorpay"] = create_razorpay_order(order)

        return Response(response, status=201)


# =====================================================
# 💳 VERIFY PAYMENT
# =====================================================

class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        payment_id = request.data.get("payment_id")
        signature = request.data.get("signature")

        order = get_object_or_404(Order, id=order_id)

        if not verify_payment_signature(order.razorpay_order_id, payment_id, signature):
            return Response({"message": "Verification failed"}, status=400)

        mark_payment_success(order, payment_id)

        OrderStatusHistory.objects.create(
            order=order, status="Processing", notes="Online payment verified"
        )
        return Response({"message": "Payment successful"})


# =====================================================
# 🔄 RETRY PAYMENT
# =====================================================

class RetryPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.payment_method != "prepaid":
            return Response({"message": "Invalid payment method"}, status=400)
        if order.payment_status == "Paid":
            return Response({"message": "Already paid"}, status=400)

        order.razorpay_order_id = None
        order.razorpay_payment_id = None
        order.save()

        razorpay_data = create_razorpay_order(order)
        return Response({"message": "Retry initiated", "razorpay": razorpay_data})


# =====================================================
# 🔗 WEBHOOK
# =====================================================

class RazorpayWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get("X-Razorpay-Signature")
        if not verify_webhook_signature(request.body, signature):
            return Response({"message": "Invalid webhook"}, status=400)
        handle_webhook(request.body)
        return Response({"status": "ok"})


# =====================================================
# 💸 REFUND
# =====================================================

class RefundOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        if not request.user.is_staff:
            return Response({"message": "Admin only"}, status=403)

        if refund_payment(order):
            OrderStatusHistory.objects.create(order=order, status="Refunded", notes="Refunded")
            return Response({"message": "Refund successful"})
        return Response({"message": "Refund failed"}, status=400)


# =====================================================
# 📲 DELIVERY OTP SYSTEM
# =====================================================

class SendDeliveryOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        if order.status not in ["shipped", "out_for_delivery"]:
            order.status = "out_for_delivery"
            order.save()

        otp = generate_otp()
        order.delivery_otp_hash = hash_otp(otp)
        order.delivery_otp_created_at = timezone.now()
        order.save()

        sms_status=send_sms(
            order.user.mobile_number,
            f"Your ITRIK delivery OTP is {otp}"
        )

        print(f"📲 OTP SENT → {otp} | Mobile: {order.user.mobile_number} | Success: {sms_status}")

        OrderStatusHistory.objects.create(
            order=order,
            status="out_for_delivery",
            notes="OTP sent to customer"
        )

        return Response({"message": "OTP sent"})


class VerifyDeliveryOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        otp = request.data.get("otp")
        order = get_object_or_404(Order, id=order_id)

        if not order.delivery_otp_created_at:
            return Response({"message": "OTP expired"}, status=400)

        if timezone.now() > order.delivery_otp_created_at + timedelta(minutes=10):
            return Response({"message": "OTP expired"}, status=400)     

        if not otp or order.delivery_otp_hash != hash_otp(otp):
            return Response({"message": "Invalid OTP"}, status=400)

        order.status = "delivered"
        order.otp_verified = True
        order.delivery_otp_hash = None

        if order.payment_method == "cod":
            order.payment_status = "paid"

        order.save()

        OrderStatusHistory.objects.create(
            order=order,
            status="delivered",
            notes="Delivered via OTP"
        )

        return Response({"message": "Delivered successfully"})

# =====================================================
# 🔧 ADMIN UPDATE STATUS
# =====================================================

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        if not request.user.is_staff:
            return Response({"message": "Admin only"}, status=403)

        order = get_object_or_404(Order, id=order_id)
        new_status = request.data.get("status")
        
        valid_statuses = [
            "processing",
            "shipped",
            "out_for_delivery",
            "delivered",
            "cancelled",
            "refunded"
        ]
        if new_status not in valid_statuses:
            return Response({"message": "Invalid status"}, status=400)

        order.status = new_status
        order.save()

        OrderStatusHistory.objects.create(
            order=order, status=new_status, notes=request.data.get("notes", "Admin Update")
        )
        return Response(OrderDetailSerializer(order).data)
 
# =====================================================
# 🚚 DELIVERY AGENT PANEL API — FIXED STATUS MATCHING
# =====================================================
class DeliveryPendingOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            status="out_for_delivery"
        ).select_related("user").prefetch_related("items__product")

        data = []

        for o in orders:
            data.append({
                "order_id": str(o.id),
                "customer_name": o.user.full_name or "Customer",
                "email": o.user.email,
                "mobile": o.user.mobile_number,
                "address": o.shipping_address_snapshot,
                "pincode": o.delivery_pincode,
                "total_amount": o.total_amount,
                "products": [
                    {
                        "name": item.product.title,
                        "qty": item.quantity
                    }
                    for item in o.items.all()
                ]
            })

        return Response(data)
    
class DeliveryCompletedOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            status="delivered"
        ).order_by("-id")

        return Response([
            {
                "id": str(o.id),
                "customer_name": o.user.full_name or "Customer",
                "mobile": o.user.mobile_number,
                "address": o.shipping_address_snapshot,
                "total_amount": o.total_amount,
                "status": o.status,
                "delivered_at": o.delivered_at,
            }
            for o in orders
        ])


class DeliveryCancelledOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            status="cancelled"
        ).order_by("-id")

        return Response([
            {
                "id": str(o.id),
                "customer_name": o.user.full_name or "Customer",
                "mobile": o.user.mobile_number,
                "address": o.shipping_address_snapshot,
                "pincode": o.delivery_pincode,
                "total_amount": o.total_amount,
                "status": o.status,
                "cancel_reason": o.cancel_reason,
            }
            for o in orders
        ])
    

class DeliveryAgentCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        reason = request.data.get("reason")

        if not reason:
            reason = "Cancelled by delivery agent"

        order.status = "cancelled"
        order.cancel_reason = reason
        order.save()

        OrderStatusHistory.objects.create(
            order=order,
            status="Cancelled",
            notes=f"Cancelled by delivery agent: {reason}"
        )

        return Response({"message": "Order cancelled successfully"})