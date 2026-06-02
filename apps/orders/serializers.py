from rest_framework import serializers
from .models import CartItem, Wishlist, Order, OrderItem, OrderStatusLog
from .constants import OrderStatus, PaymentMethod, DeliveryZone

# ─── Cart ─────────────────────────────────────────────────────────────────────

class CartProductSerializer(serializers.Serializer):
    """Lightweight product snapshot for cart."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField() 
    primary_image = serializers.SerializerMethodField() 
    regular_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True
    )
    stock_quantity = serializers.IntegerField()
    is_active = serializers.BooleanField()

    def get_primary_image(self, obj) -> str | None:
        request = self.context.get("request")
        if hasattr(obj, 'images'):
            primary = next((img for img in obj.images.all() if img.is_primary), None)
            if not primary:
                primary = next(iter(obj.images.all()), None)
            if primary and primary.image:
                if request:
                    return request.build_absolute_uri(primary.image.url)
                return primary.image.url
        return None



class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    unit_price = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_unit_price(self, obj) -> float:
        p = obj.product
        return float(p.discount_price if p.discount_price else p.regular_price)

    def get_line_total(self, obj) -> float:
        p = obj.product
        unit = p.discount_price if p.discount_price else p.regular_price
        return float(unit * obj.quantity)


class CartSummarySerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    item_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)


# ─── Wishlist ─────────────────────────────────────────────────────────────────

class WishlistProductSerializer(serializers.Serializer):
    """Lightweight product snapshot for wishlist."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField() # <-- এটি যুক্ত করা হলো
    category_name = serializers.CharField(source="category.name", read_only=True) # <-- এটি যুক্ত করা হলো
    primary_image = serializers.SerializerMethodField() # <-- এটি যুক্ত করা হলো
    regular_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, allow_null=True
    )
    stock_quantity = serializers.IntegerField()
    is_active = serializers.BooleanField()
    is_in_stock = serializers.BooleanField(read_only=True) # <-- ProductCard এর জন্য এটিও দরকার
    final_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True) # <-- ProductCard এর জন্য এটিও দরকার

    def get_primary_image(self, obj) -> str | None:
        request = self.context.get("request")
        # Product মডেলে 'images' নামে related_name আছে ধরে নেওয়া হলো
        if hasattr(obj, 'images'):
            primary = next((img for img in obj.images.all() if img.is_primary), None)
            if not primary:
                primary = next(iter(obj.images.all()), None)
            if primary and primary.image:
                if request:
                    return request.build_absolute_uri(primary.image.url)
                return primary.image.url
        return None


class WishlistSerializer(serializers.ModelSerializer):
    product = WishlistProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product", "product_id", "created_at"]
        read_only_fields = ["id", "created_at"]


# ─── Checkout ─────────────────────────────────────────────────────────────────

class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(min_length=10, max_length=1000)
    delivery_zone = serializers.ChoiceField(choices=DeliveryZone.CHOICES)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.CHOICES)

    def validate_shipping_address(self, value: str) -> str:
        return value.strip()


# ─── Order ────────────────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="product.id")
    product_name = serializers.CharField(source="product.name")
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "quantity",
            "price",
            "line_total",
        ]

    def get_line_total(self, obj) -> float:
        return float(obj.line_total)


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusLog
        fields = ["id", "old_status", "new_status", "changed_by_email", "created_at"]

    def get_changed_by_email(self, obj) -> str | None:
        return obj.changed_by.email if obj.changed_by else None


class OrderListSerializer(serializers.ModelSerializer):
    """Compact serializer for order list endpoints."""
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "order_number",
            "status",
            "payment_method",
            "total_amount",
            "delivery_charge",
            "item_count",
            "courier_name",
            "tracking_id",
            "created_at",
        ]

    def get_item_count(self, obj) -> int:
        # Uses prefetched items if available
        if hasattr(obj, "_prefetched_objects_cache") and "items" in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache["items"])
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for single order view."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_number",
            "user_email",
            "status",
            "payment_method",
            "subtotal",
            "delivery_charge",
            "total_amount",
            "shipping_address",
            "courier_name",
            "tracking_id",
            "invoice_url",
            "items",
            "status_logs",
            "created_at",
            "updated_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    """Base serializer — used internally."""

    class Meta:
        model = Order
        fields = "__all__"


class AdminOrderStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=OrderStatus.CHOICES)