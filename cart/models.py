from django.db import models
from django.contrib.auth import get_user_model
from store.models import Product
import uuid

User = get_user_model()


class Cart(models.Model):
    """
    Shopping cart (guest + logged users).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # For logged in users
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True
    )

    # For guest users (session based)
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    def __str__(self):
        if self.user:
            return f"Cart of {self.user}"
        return f"Guest Cart {self.session_key}"

    # ============================
    # TOTALS
    # ============================

    def get_total_price(self):
        return sum(item.get_subtotal() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    # ============================
    # CART OPS
    # ============================

    def remove_product(self, product):
        self.items.filter(product=product).delete()

    def clear(self):
        self.items.all().delete()

    # ============================
    # MERGE GUEST → USER CART
    # ============================

    def merge_into(self, user_cart):
        """
        Merge guest cart items into user cart on login
        """

        for item in self.items.all():
            existing = user_cart.items.filter(product=item.product).first()

            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                item.cart = user_cart
                item.save()

        self.delete()


class CartItem(models.Model):
    """
    Individual product in cart.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )

    quantity = models.PositiveIntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "product")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.product.title} × {self.quantity}"

    # ============================
    # PRICE
    # ============================

    def get_subtotal(self):
        price = self.product.discount_price or self.product.price
        return price * self.quantity

    # ============================
    # QUANTITY OPS
    # ============================

    def increase(self, amount=1):
        self.quantity += amount
        self.save()

    def decrease(self, amount=1):
        self.quantity -= amount
        if self.quantity <= 0:
            self.delete()
        else:
            self.save()
