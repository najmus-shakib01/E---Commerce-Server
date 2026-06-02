from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.urls import reverse, NoReverseMatch
from apps.core.response import api_response
from .models import Order, CartItem, Wishlist

class OrderAPIRootView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  

    def get(self, request):
        sample_order = Order.objects.order_by("-created_at").first()
        sample_cart_item = CartItem.objects.first()
        sample_wishlist = Wishlist.objects.first()

        sample_order_number = (
            sample_order.order_number if sample_order else "ORD-2026-000001"
        )
        sample_cart_id = (
            str(sample_cart_item.id)
            if sample_cart_item
            else "00000000-0000-0000-0000-000000000000"
        )
        sample_wishlist_id = (
            str(sample_wishlist.id)
            if sample_wishlist
            else "00000000-0000-0000-0000-000000000000"
        )

        def build(name, **kwargs):
            try:
                return request.build_absolute_uri(
                    reverse(f"orders:{name}", kwargs=kwargs)
                )
            except NoReverseMatch:
                return None

        endpoints = {
            "module": "Orders, Cart & Wishlist",
            "version": "v1",
            "base_url": request.build_absolute_uri("/api/v1/orders/"),
            "authentication_note": "All endpoints below require: Authorization: Bearer <access_token>",
            "cart": {
                "get_cart": {
                    "url": build("cart"),
                    "method": "GET",
                    "auth": True,
                },
                "add_to_cart": {
                    "url": build("cart-add"),
                    "method": "POST",
                    "auth": True,
                    "body": {"product_id": "uuid", "quantity": 1},
                },
                "update_item": {
                    "url": build("cart-item-update", id=sample_cart_id),
                    "method": "PATCH",
                    "auth": True,
                    "body": {"quantity": 2},
                },
                "delete_item": {
                    "url": build("cart-item-delete", id=sample_cart_id),
                    "method": "DELETE",
                    "auth": True,
                },
                "clear_cart": {
                    "url": build("cart-clear"),
                    "method": "DELETE",
                    "auth": True,
                },
            },
            "wishlist": {
                "list_wishlist": {
                    "url": build("wishlist"),
                    "method": "GET",
                    "auth": True,
                },
                "add_wishlist": {
                    "url": build("wishlist-add"),
                    "method": "POST",
                    "auth": True,
                    "body": {"product_id": "uuid"},
                },
                "remove_wishlist": {
                    "url": build("wishlist-delete", id=sample_wishlist_id),
                    "method": "DELETE",
                    "auth": True,
                },
                "move_to_cart": {
                    "url": build("wishlist-move", id=sample_wishlist_id),
                    "method": "POST",
                    "auth": True,
                },
            },
            "checkout": {
                "checkout": {
                    "url": build("checkout"),
                    "method": "POST",
                    "auth": True,
                    "body": {
                        "shipping_address": "string (min 10 chars)",
                        "delivery_zone": "inside | outside",
                        "payment_method": "COD | MANUAL_MFS",
                    },
                },
            },
            "orders": {
                "list_orders": {
                    "url": build("order-list"),
                    "method": "GET",
                    "auth": True,
                    "filters": "?status=PENDING&payment_method=COD&created_after=2026-01-01&ordering=-created_at",
                },
                "order_detail": {
                    "url": build("order-detail", order_number=sample_order_number),
                    "method": "GET",
                    "auth": True,
                },
                "cancel_order": {
                    "url": build("order-cancel", order_number=sample_order_number),
                    "method": "POST",
                    "auth": True,
                    "note": "Only PENDING orders can be cancelled",
                },
            },
            "admin": {
                "update_status": {
                    "url": build("admin-order-status", order_number=sample_order_number),
                    "method": "PATCH",
                    "auth": True,
                    "admin_only": True,
                    "body": {
                        "new_status": "CONFIRMED | SHIPPED | DELIVERED | CANCELLED"
                    },
                },
            },
        }

        return api_response(True, "Orders Module API Root", endpoints, 200)