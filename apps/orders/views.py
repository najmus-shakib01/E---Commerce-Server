from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from apps.core.response import api_response
from apps.core.pagination import StandardResultsSetPagination
from .serializers import (
    CartItemSerializer,
    CartSummarySerializer,
    WishlistSerializer,
    CheckoutSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    AdminOrderStatusUpdateSerializer,
)
from .services import (
    # Cart
    add_to_cart,
    update_cart_quantity,
    remove_cart_item,
    clear_cart,
    get_cart_summary,
    # Wishlist
    add_to_wishlist,
    remove_from_wishlist,
    move_wishlist_to_cart,
    # Orders
    create_order,
    cancel_order,
    update_order_status,
    get_order_details,
    list_user_orders,
)
from .models import Wishlist
from .filters import OrderFilter


# ══════════════════════════════════════════════════════════════════════════════
# CART VIEWS
# ══════════════════════════════════════════════════════════════════════════════

class CartView(APIView):
    """GET /cart/ — Retrieve current user's cart summary."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        summary = get_cart_summary(request.user)
        # ✅ context={"request": request} যুক্ত করা হয়েছে ইমেজের জন্য
        serializer = CartSummarySerializer(summary, context={"request": request})
        return api_response(True, "Cart retrieved successfully.", serializer.data, 200)

class CartAddView(APIView):
    """POST /cart/add/ — Add item to cart."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        cart_item = add_to_cart(request.user, product_id, quantity)
        # ✅ ডাবল সিরিয়ালাইজার রিমুভ করে সঠিকটি রাখা হয়েছে
        serializer = CartItemSerializer(cart_item, context={"request": request})
        return api_response(True, "Item added to cart.", serializer.data, 201)


class CartItemUpdateView(APIView):
    """PATCH /cart/items/<id>/ — Update cart item quantity."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        quantity = int(request.data.get("quantity", 1))
        cart_item = update_cart_quantity(request.user, str(id), quantity)
        # ✅ ডাবল সিরিয়ালাইজার রিমুভ করে সঠিকটি রাখা হয়েছে
        serializer = CartItemSerializer(cart_item, context={"request": request})
        return api_response(True, "Cart item updated.", serializer.data, 200)

class CartItemDeleteView(APIView):
    """DELETE /cart/items/<id>/ — Remove a single cart item."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        remove_cart_item(request.user, str(id))
        return api_response(True, "Item removed from cart.", None, 200)


class CartClearView(APIView):
    """DELETE /cart/clear/ — Remove all cart items."""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        clear_cart(request.user)
        return api_response(True, "Cart cleared.", None, 200)


# ══════════════════════════════════════════════════════════════════════════════
# WISHLIST VIEWS
# ══════════════════════════════════════════════════════════════════════════════

class WishlistView(APIView):
    """GET /wishlist/ — List all wishlist items for the user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ✅ আগের ভুল কার্ট কোডটি রিমুভ করে আসল উইশলিস্ট কোড বসানো হয়েছে
        items = Wishlist.objects.for_user(request.user)
        serializer = WishlistSerializer(items, many=True, context={"request": request})
        return api_response(True, "Wishlist retrieved.", serializer.data, 200)


class WishlistAddView(APIView):
    """POST /wishlist/add/ — Add product to wishlist."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        item = add_to_wishlist(request.user, product_id)
        serializer = WishlistSerializer(item, context={"request": request})
        return api_response(True, "Added to wishlist.", serializer.data, 201)


class WishlistDeleteView(APIView):
    """DELETE /wishlist/<id>/ — Remove item from wishlist."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        remove_from_wishlist(request.user, str(id))
        return api_response(True, "Removed from wishlist.", None, 200)


class WishlistMoveToCartView(APIView):
    """POST /wishlist/<id>/move-to-cart/ — Move wishlist item to cart."""
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        cart_item = move_wishlist_to_cart(request.user, str(id))
        serializer = CartItemSerializer(cart_item, context={"request": request})
        return api_response(True, "Item moved to cart.", serializer.data, 200)


# ══════════════════════════════════════════════════════════════════════════════
# CHECKOUT VIEW
# ══════════════════════════════════════════════════════════════════════════════

class CheckoutView(APIView):
    """POST /checkout/ — Place an order from cart."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = create_order(
            user=request.user,
            shipping_address=serializer.validated_data["shipping_address"],
            delivery_zone=serializer.validated_data["delivery_zone"],
            payment_method=serializer.validated_data["payment_method"],
        )
        detail_serializer = OrderDetailSerializer(order, context={"request": request})
        return api_response(True, "Order placed successfully.", detail_serializer.data, 201)


# ══════════════════════════════════════════════════════════════════════════════
# ORDER VIEWS (USER)
# ══════════════════════════════════════════════════════════════════════════════

class OrderListView(APIView):
    """GET /orders/ — List all orders for authenticated user with filters."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = list_user_orders(request.user)

        filterset = OrderFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return api_response(False, "Invalid filters.", filterset.errors, 400)
        queryset = filterset.qs

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = OrderListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class OrderDetailView(APIView):
    """GET /orders/<order_number>/ — Get full order detail."""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = get_order_details(request.user, order_number)
        serializer = OrderDetailSerializer(order, context={"request": request})
        return api_response(True, "Order details retrieved.", serializer.data, 200)


class OrderCancelView(APIView):
    """POST /orders/<order_number>/cancel/ — Cancel a pending order."""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        order = cancel_order(request.user, order_number)
        serializer = OrderDetailSerializer(order, context={"request": request})
        return api_response(True, "Order cancelled successfully.", serializer.data, 200)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN VIEWS
# ══════════════════════════════════════════════════════════════════════════════

class AdminOrderStatusUpdateView(APIView):
    """PATCH /admin/orders/<order_number>/status/ — Admin updates order status."""
    permission_classes = [IsAdminUser]

    def patch(self, request, order_number):
        serializer = AdminOrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = update_order_status(
            admin_user=request.user,
            order_number=order_number,
            new_status=serializer.validated_data["new_status"],
        )
        detail_serializer = OrderDetailSerializer(order, context={"request": request})
        return api_response(True, "Order status updated.", detail_serializer.data, 200)
