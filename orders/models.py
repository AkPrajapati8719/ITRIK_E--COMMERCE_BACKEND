from django.db import models
from django.contrib.auth import get_user_model
from store.models import Product
from django.utils import timezone
import uuid
from datetime import timedelta
from decimal import Decimal

User = get_user_model()


class Order(models.Model):
    """
    Full Amazon/Flipkart style order + payment engine
    """

    # ================= ORDER STATUS =================

    STATUS_CHOICES = [
        ("pending_payment", "Pending Payment"),
        ("processing", "Processing"),
        ("packed", "Packed"),
        ("shipped", "Shipped"),
        ("out_for_delivery", "Out for Delivery"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("returned", "Returned"),
        ("replaced", "Replaced"),
    ]

    # ================= PAYMENT =================

    PAYMENT_METHOD_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("prepaid", "Online Payment"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending_payment"
    )

    # ================= PAYMENT INFO =================

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="cod"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    razorpay_order_id = models.CharField(max_length=150, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=150, blank=True, null=True)

    is_paid = models.BooleanField(default=False)

    # ================= PRICING =================

    items_total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # ================= DELIVERY SNAPSHOT =================

    shipping_address_snapshot = models.TextField()
    delivery_pincode = models.CharField(max_length=10)

    # ================= ETA =================

    eta_days = models.PositiveIntegerField(default=4)
    estimated_delivery_date = models.DateField(blank=True, null=True)

    # ================= DELIVERY OTP =================

    delivery_otp_hash = models.CharField(max_length=128, blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    delivery_otp_created_at = models.DateTimeField(null=True, blank=True)

    # ================= DELIVERY AGENT TRACKING =================

    delivery_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_deliveries"
    )

    delivered_at = models.DateTimeField(blank=True, null=True)

    is_cancelled = models.BooleanField(default=False)

    cancel_reason = models.TextField(blank=True, null=True)


    # ================= CANCEL / RETURN =================

    cancel_allowed_until = models.DateTimeField(blank=True, null=True)
    return_requested = models.BooleanField(default=False)
    replacement_requested = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["payment_method", "payment_status"]),
            models.Index(fields=["created_at"]),
        ]

    # =====================================================
    # CORE AUTOMATION (REAL ECOMMERCE BEHAVIOR)
    # =====================================================

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # ⏳ Cancel window (24 hrs like Amazon)
        if not self.cancel_allowed_until:
            self.cancel_allowed_until = timezone.now() + timedelta(hours=24)

        # 🚚 ETA auto calculation
        if not self.estimated_delivery_date:
            self.estimated_delivery_date = (
                timezone.now().date() + timedelta(days=self.eta_days)
            )

        # 🔐 STRICT OTP DELIVERY GUARD
        # Force status back to 'out_for_delivery' if attempted to mark delivered without OTP
        if self.status == "delivered" and not self.otp_verified:
            self.status = "out_for_delivery"

        # 💳 Payment logic sync

        # COD → paid only after delivery OTP verification
        if self.payment_method == "cod":
            if self.otp_verified and self.status == "delivered":
                self.payment_status = "paid"
                self.is_paid = True
            else:
                self.payment_status = "pending"
                self.is_paid = False

        # Online → paid by gateway confirmation
        if self.payment_method == "prepaid":
            if self.payment_status == "paid":
                self.is_paid = True
            else:
                self.is_paid = False

        # 📦 Auto mark delivery timestamp
        if self.status == "delivered" and not self.delivered_at:
            self.delivered_at = timezone.now()

        super().save(*args, **kwargs)

        # 📜 AUTO-HISTORY TIMELINE LOGGING
        if not is_new:
            last_history = self.status_history.order_by('-changed_at').first()
            if not last_history or last_history.status != self.status:
                OrderStatusHistory.objects.create(
                    order=self,
                    status=self.status,
                    notes=f"System moved order to {self.get_status_display()}"
                )

    # =====================================================
    # BUSINESS RULES
    # =====================================================

    def can_cancel(self):
        return (
            timezone.now() <= self.cancel_allowed_until
            and self.status not in ["delivered", "cancelled", "returned", "shipped", "out_for_delivery"]
        )

    # for the deliveryPartner
    def mark_delivered(self):
        self.status = "delivered"
        self.otp_verified = True
        self.delivered_at = timezone.now()
        self.save()

    def mark_cancelled(self, reason):
        self.status = "cancelled"
        self.is_cancelled = True
        self.cancel_reason = reason
        self.save()

    def mark_refunded(self, amount=None):
        self.refund_amount = amount or self.total_amount
        self.payment_status = "refunded"
        self.save()

    def __str__(self):
        return f"Order {self.id} — {self.user.email} — {self.status}"


class OrderItem(models.Model):
    """
    Each product inside an order (price locked at purchase)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items"
    )

    quantity = models.PositiveIntegerField()

    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def subtotal(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"


class OrderStatusHistory(models.Model):
    """
    Full order lifecycle tracking
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history"
    )

    status = models.CharField(
        max_length=30,
        choices=Order.STATUS_CHOICES
    )

    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["changed_at"]

    def __str__(self):
        return f"{self.order.id} → {self.status}"