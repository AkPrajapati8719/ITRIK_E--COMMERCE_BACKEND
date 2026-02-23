from django.urls import path
from .views import (
    CartView,
    AddToCartView,
    RemoveFromCartView,
    UpdateCartItemView,
    ClearCartView
)

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("add/", AddToCartView.as_view(), name="add-to-cart"),
    path("remove/", RemoveFromCartView.as_view(), name="remove-from-cart"),
    path("update/<uuid:item_id>/", UpdateCartItemView.as_view(), name="update-cart-item"),
    path("clear/", ClearCartView.as_view(), name="clear-cart"),
]

