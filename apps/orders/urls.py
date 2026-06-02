from django.urls import path
from .views import (
    # Cart
    CartView,
    CartAddView,
    CartItemUpdateView,
    CartItemDeleteView,
    CartClearView,
    # Wishlist
    WishlistView,
    WishlistAddView,
    WishlistDeleteView,
    WishlistMoveToCartView,
    # Checkout
    CheckoutView,
    # Orders
    OrderListView,
    OrderDetailView,
    OrderCancelView,
    # Admin
    AdminOrderStatusUpdateView,
)
from .APIRootView import OrderAPIRootView

app_name = "orders"

urlpatterns = [
    # ── API Root ──────────────────────────────────────────────────────────────
    path("", OrderAPIRootView.as_view(), name="api-root"),

    # ── Cart ──────────────────────────────────────────────────────────────────
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", CartAddView.as_view(), name="cart-add"),
    path("cart/items/<uuid:id>/", CartItemUpdateView.as_view(), name="cart-item-update"),
    path("cart/items/<uuid:id>/delete/", CartItemDeleteView.as_view(), name="cart-item-delete"),
    path("cart/clear/", CartClearView.as_view(), name="cart-clear"),

    # ── Wishlist ──────────────────────────────────────────────────────────────
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("wishlist/add/", WishlistAddView.as_view(), name="wishlist-add"),
    path("wishlist/<uuid:id>/", WishlistDeleteView.as_view(), name="wishlist-delete"),
    path("wishlist/<uuid:id>/move-to-cart/", WishlistMoveToCartView.as_view(), name="wishlist-move"),

    # ── Checkout ──────────────────────────────────────────────────────────────
    path("checkout/", CheckoutView.as_view(), name="checkout"),

    # ── Orders (User) ─────────────────────────────────────────────────────────
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<str:order_number>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<str:order_number>/cancel/", OrderCancelView.as_view(), name="order-cancel"),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path("admin/orders/<str:order_number>/status/", AdminOrderStatusUpdateView.as_view(), name="admin-order-status"),
]