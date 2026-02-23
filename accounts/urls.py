from django.urls import path
from .views import (
    SendOTPView,
    VerifyOTPView,
    ProfileView,
    DeliveryLoginView
)

urlpatterns = [
    # 👤 Customer OTP login
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),

    # 🚚 Delivery partner password login
    path("delivery-login/", DeliveryLoginView.as_view(), name="delivery-login"),

    # 👤 Customer profile
    path("profile/", ProfileView.as_view(), name="profile"),
]
