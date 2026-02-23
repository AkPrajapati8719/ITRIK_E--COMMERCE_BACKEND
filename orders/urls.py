from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet,
    CreateOrderView,
    ShippingPreviewView,
    VerifyPaymentView,
    RazorpayWebhookView,
    RefundOrderView,
    RetryPaymentView,
    SendDeliveryOTPView,
    VerifyDeliveryOTPView,
    UpdateOrderStatusView,

    # 🚚 Delivery Agent Views
    DeliveryPendingOrdersView,
    DeliveryCompletedOrdersView,
    DeliveryCancelledOrdersView,
    DeliveryAgentCancelView,
)

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [

    # ===========================
    # 📦 USER ORDER LIST & DETAILS
    # ===========================
    path("", include(router.urls)),

    # ===========================
    # 🚚 SHIPPING PREVIEW
    # ===========================
    path(
        "shipping-preview/",
        ShippingPreviewView.as_view(),
        name="shipping-preview"
    ),

    # ===========================
    # 🛒 CREATE ORDER
    # ===========================
    path(
        "create/",
        CreateOrderView.as_view(),
        name="create-order"
    ),

    # ===========================
    # 💳 ONLINE PAYMENT FLOW
    # ===========================
    path(
        "verify-payment/",
        VerifyPaymentView.as_view(),
        name="verify-payment"
    ),

    path(
        "<uuid:order_id>/retry-payment/",
        RetryPaymentView.as_view(),
        name="retry-payment"
    ),

    path(
        "razorpay/webhook/",
        RazorpayWebhookView.as_view(),
        name="razorpay-webhook"
    ),

    path(
        "<uuid:order_id>/refund/",
        RefundOrderView.as_view(),
        name="refund-order"
    ),

    # ===========================
    # 📲 DELIVERY OTP (USER / ADMIN)
    # ===========================
    path(
        "<uuid:order_id>/send-otp/",
        SendDeliveryOTPView.as_view(),
        name="send-delivery-otp"
    ),

    path(
        "<uuid:order_id>/verify-otp/",
        VerifyDeliveryOTPView.as_view(),
        name="verify-delivery-otp"
    ),

    # ===========================
    # 🔧 ADMIN STATUS CONTROL
    # ===========================
    path(
        "<uuid:order_id>/update-status/",
        UpdateOrderStatusView.as_view(),
        name="update-order-status"
    ),

    # ======================================================
    # 🚚 DELIVERY AGENT PANEL API (MATCHES FRONTEND EXACTLY)
    # ======================================================

    path(
        "delivery/pending/",
        DeliveryPendingOrdersView.as_view(),
        name="delivery-pending-orders"
    ),

    path(
        "delivery/completed/",
        DeliveryCompletedOrdersView.as_view(),
        name="delivery-completed-orders"
    ),

    path(
        "delivery/cancelled/",
        DeliveryCancelledOrdersView.as_view(),
        name="delivery-cancelled-orders"
    ),

    path(
        "delivery/<uuid:order_id>/cancel/",
        DeliveryAgentCancelView.as_view(),
        name="delivery-agent-cancel"
    ),

    # Delivery panel OTP endpoints (alias support)
    path(
        "delivery/<uuid:order_id>/send-otp/",
        SendDeliveryOTPView.as_view(),
        name="delivery-panel-send-otp"
    ),

    path(
        "delivery/<uuid:order_id>/verify-otp/",
        VerifyDeliveryOTPView.as_view(),
        name="delivery-panel-verify-otp"
    ),
]