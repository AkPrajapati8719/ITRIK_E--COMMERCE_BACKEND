from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import random

from cart.models import Cart, CartItem
from store.models import Product

from .models import OTPCode
from .serializers import UserSerializer, ProfileUpdateSerializer

User = get_user_model()


# ======================================================
# 🛠 UTILITIES
# ======================================================

def generate_otp():
    return str(random.randint(100000, 999999))


def send_sms_simulation(mobile, otp):
    print(f"\n📲 [SMS LOGIN] {mobile} | OTP: {otp}\n")


# ======================================================
# 📩 CUSTOMER OTP LOGIN
# ======================================================

class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier")

        if not identifier:
            return Response({"error": "Email or mobile required"}, status=400)

        is_email = "@" in identifier
        is_mobile = identifier.isdigit() and len(identifier) == 10

        if not (is_email or is_mobile):
            return Response({"error": "Invalid email or mobile"}, status=400)

        # Block OTP for delivery partners
        user = (
            User.objects.filter(email=identifier).first()
            if is_email else
            User.objects.filter(mobile_number=identifier).first()
        )

        if user and user.is_delivery_partner:
            return Response(
                {"error": "Delivery partners must login with password"},
                status=403
            )

        # Create customer if not exists
        if not user:
            if is_email:
                user = User.objects.create_user(email=identifier)
            else:
                user = User.objects.create_user(
                    email=f"{identifier}@temp.itrik.com",
                    mobile_number=identifier
                )

        otp = generate_otp()

        OTPCode.objects.update_or_create(
            identifier=identifier,
            defaults={
                "code": otp,
                "attempts": 0,
                "created_at": timezone.now()
            }
        )

        # Send OTP
        if is_email:
            try:
                send_mail(
                    "Your ITRIK Login OTP",
                    f"Your OTP is {otp}. Valid for 5 minutes.",
                    settings.DEFAULT_FROM_EMAIL,
                    [identifier],
                )
            except Exception:
                return Response({"error": "Email failed"}, status=500)
        else:
            send_sms_simulation(identifier, otp)

        return Response({"success": True})


# ======================================================
# 🔐 VERIFY OTP (CUSTOMER)
# ======================================================

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("identifier")
        otp_code = request.data.get("otp_code")

        if not identifier or not otp_code:
            return Response({"error": "OTP required"}, status=400)

        try:
            otp_obj = OTPCode.objects.get(identifier=identifier)
        except OTPCode.DoesNotExist:
            return Response({"error": "OTP not found"}, status=400)

        if otp_obj.is_expired():
            otp_obj.delete()
            return Response({"error": "OTP expired"}, status=400)

        if otp_obj.code != otp_code:
            otp_obj.attempts += 1
            otp_obj.save(update_fields=["attempts"])

            if otp_obj.attempts >= 5:
                otp_obj.delete()
                return Response({"error": "Too many attempts"}, status=400)

            return Response({"error": "Invalid OTP"}, status=400)

        otp_obj.delete()

        user = (
            User.objects.get(email=identifier)
            if "@" in identifier else
            User.objects.get(mobile_number=identifier)
        )

        user.is_verified = True
        user.save(update_fields=["is_verified"])

        # 🛒 Merge cart
        session_cart = request.session.get("cart", {})

        if session_cart:
            cart, _ = Cart.objects.get_or_create(user=user)

            for product_id, data in session_cart.items():
                qty = data if isinstance(data, int) else data.get("quantity", 0)
                if qty <= 0:
                    continue

                product = Product.objects.filter(id=product_id).first()
                if not product:
                    continue

                item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={"quantity": qty}
                )

                if not created:
                    item.quantity = min(item.quantity + qty, product.stock)
                    item.save()

            request.session["cart"] = {}
            request.session.modified = True

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "user": UserSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })


# ======================================================
# 🚚 DELIVERY PARTNER PASSWORD LOGIN
# ======================================================

class DeliveryLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        user = authenticate(request, username=email, password=password)

        if not user or not user.is_delivery_partner:
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "role": "delivery_partner"
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })


# ======================================================
# 👤 PROFILE (CUSTOMER ONLY)
# ======================================================
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def put(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "user": UserSerializer(request.user).data
        })