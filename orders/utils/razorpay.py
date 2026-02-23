import razorpay
import hmac
import hashlib
import json
import logging
from decimal import Decimal
from django.conf import settings
from orders.models import Order

logger = logging.getLogger(__name__)

# =====================================================
# RAZORPAY CLIENT (SAFE INIT)
# =====================================================

client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)

# =====================================================
# CREATE RAZORPAY PAYMENT ORDER
# =====================================================

def create_razorpay_order(order: Order):
    """
    Creates Razorpay payment order for prepaid checkout
    """

    if order.payment_method != "prepaid":
        raise ValueError("Only prepaid orders allowed")

    if order.payment_status == "paid":
        raise ValueError("Order already paid")

    if order.razorpay_order_id:
        return {
            "id": order.razorpay_order_id,
            "amount": int(order.total_amount * 100),
            "currency": "INR"
        }

    amount_paise = int(order.total_amount * Decimal("100"))

    data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": str(order.id),
        "payment_capture": 1,
    }

    try:
        razorpay_order = client.order.create(data=data)

        order.razorpay_order_id = razorpay_order["id"]
        order.save(update_fields=["razorpay_order_id"])

        return razorpay_order

    except Exception as e:
        logger.exception("Razorpay order creation failed")
        raise RuntimeError("Payment service unavailable")

# =====================================================
# VERIFY PAYMENT SIGNATURE (ANTI FRAUD)
# =====================================================

def verify_payment_signature(order_id, payment_id, signature):

    payload = f"{order_id}|{payment_id}"

    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        generated_signature,
        signature
    )

# =====================================================
# MARK PAYMENT SUCCESS (IDEMPOTENT)
# =====================================================

def mark_payment_success(order: Order, payment_id):

    if order.payment_status == "paid":
        return

    order.razorpay_payment_id = payment_id
    order.payment_status = "paid"
    order.is_paid = True

    if order.status == "pending_payment":
        order.status = "processing"

    order.save(update_fields=[
        "razorpay_payment_id",
        "payment_status",
        "is_paid",
        "status"
    ])

# =====================================================
# MARK PAYMENT FAILURE
# =====================================================

def mark_payment_failed(order: Order):

    if order.payment_status == "paid":
        return

    order.payment_status = "failed"
    order.is_paid = False
    order.save(update_fields=["payment_status", "is_paid"])

# =====================================================
# VERIFY WEBHOOK SIGNATURE (CRITICAL SECURITY)
# =====================================================

def verify_webhook_signature(payload: bytes, signature: str):

    if not signature:
        return False

    secret = settings.RAZORPAY_WEBHOOK_SECRET.encode()

    generated_signature = hmac.new(
        secret,
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        generated_signature,
        signature
    )

# =====================================================
# HANDLE WEBHOOK EVENTS (SAFE & IDEMPOTENT)
# =====================================================

def handle_webhook(payload: bytes):

    try:
        event = json.loads(payload)
    except Exception:
        logger.error("Invalid Razorpay webhook payload")
        return

    payment_entity = (
        event.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )

    razorpay_order_id = payment_entity.get("order_id")
    payment_id = payment_entity.get("id")
    status = payment_entity.get("status")

    if not razorpay_order_id:
        logger.error("Webhook missing order_id")
        return

    try:
        order = Order.objects.get(
            razorpay_order_id=razorpay_order_id
        )
    except Order.DoesNotExist:
        logger.error("Webhook order not found")
        return

    if status == "captured":
        mark_payment_success(order, payment_id)

    elif status in ["failed", "cancelled"]:
        mark_payment_failed(order)

# =====================================================
# REFUND PAYMENT (FULL / PARTIAL)
# =====================================================

def refund_payment(order: Order, amount=None):

    if not order.razorpay_payment_id:
        raise ValueError("No payment available to refund")

    if order.payment_status == "refunded":
        return False

    refund_amount = amount or order.total_amount
    refund_paise = int(refund_amount * Decimal("100"))

    try:
        client.payment.refund(
            order.razorpay_payment_id,
            {
                "amount": refund_paise
            }
        )

        order.mark_refunded(refund_amount)

        return True

    except Exception:
        logger.exception("Razorpay refund failed")
        return False
