from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta
import uuid


# =====================================================
# 👤 USER MANAGER
# =====================================================

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # Customers default → OTP only (no password)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.is_active = True
        user.save(using=self._db)
        return user

    def create_delivery_partner(self, email, password, **extra_fields):
        """
        Admin-only creation of delivery staff
        """
        extra_fields.setdefault("is_delivery_partner", True)
        return self.create_user(email=email, password=password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, password=password, **extra_fields)


# =====================================================
# 👤 USER MODEL
# =====================================================

class User(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)

    full_name = models.CharField(max_length=255, blank=True)

    mobile_number = models.CharField(max_length=10, blank=True, null=True)
    alternate_mobile = models.CharField(max_length=10, blank=True, null=True)

    shipping_address = models.TextField(blank=True, null=True)
    delivery_pincode = models.CharField(max_length=6, blank=True, null=True)

    # 🚚 Delivery role
    is_delivery_partner = models.BooleanField(default=False)

    # 👤 Customer flow
    is_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)

    # Django auth fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# =====================================================
# 🔐 OTP MODEL (CUSTOMER LOGIN ONLY)
# =====================================================

class OTPCode(models.Model):

    identifier = models.CharField(
        max_length=255,
        db_index=True
    )  # email or mobile

    code = models.CharField(max_length=6)

    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.IntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.identifier} | {self.code}"
