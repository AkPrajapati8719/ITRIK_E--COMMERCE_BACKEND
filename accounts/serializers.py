from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import OTPCode

User = get_user_model()


# =====================================================
# 👤 USER OUTPUT (SAFE)
# =====================================================

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "mobile_number",
            "alternate_mobile",
            "shipping_address",
            "delivery_pincode",
            "is_verified",
            "profile_completed",
            "is_delivery_partner",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "is_verified",
            "profile_completed",
            "is_delivery_partner",
            "created_at",
        ]


# =====================================================
# 📩 OTP INPUT
# =====================================================

class SendOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)


# =====================================================
# 👤 PROFILE UPDATE
# =====================================================

class ProfileUpdateSerializer(serializers.ModelSerializer):

    delivery_pincode = serializers.CharField(max_length=6)

    class Meta:
        model = User
        fields = [
            "full_name",
            "mobile_number",
            "alternate_mobile",
            "shipping_address",
            "delivery_pincode",
        ]

    def validate_delivery_pincode(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Enter a valid 6-digit pincode")
        return value

    def update(self, instance, validated_data):

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.profile_completed = all([
            instance.full_name,
            instance.mobile_number,
            instance.shipping_address,
            instance.delivery_pincode,
        ])

        instance.save()
        return instance
