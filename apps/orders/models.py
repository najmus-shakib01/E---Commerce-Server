import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from .constants import OrderStatus, PaymentMethod
from .managers import CartItemManager, WishlistManager, OrderManager
User = get_user_model()

# ─── Cart Item ────────────────────────────────────────────────────────────────
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items",
    )
    product = models.ForeignKey(
        "product.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CartItemManager()

    class Meta:
        db_table = "cart_items"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"], name="idx_cart_user"),
            models.Index(fields=["product"], name="idx_cart_product"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                condition=models.Q(user__isnull=False),
                name="unique_user_product_cart",
            )
        ]

    def __str__(self):
        return f"Cart: {self.user_id} | Product: {self.product_id} | Qty: {self.quantity}"


# ─── Wishlist ─────────────────────────────────────────────────────────────────
class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )
    product = models.ForeignKey(
        "product.Product",
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = WishlistManager()

    class Meta:
        db_table = "wishlists"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"], name="idx_wishlist_user"),
            models.Index(fields=["product"], name="idx_wishlist_product"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_user_product_wishlist",
            )
        ]

    def __str__(self):
        return f"Wishlist: {self.user_id} | Product: {self.product_id}"


# ─── Order ────────────────────────────────────────────────────────────────────
class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        db_index=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    shipping_address = models.TextField()
    delivery_charge = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.CHOICES,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.CHOICES,
    )
    invoice_url = models.CharField(max_length=500, null=True, blank=True)
    courier_name = models.CharField(max_length=100, null=True, blank=True)
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_order_user_status"),
            models.Index(fields=["created_at"], name="idx_order_created"),
        ]

    def __str__(self):
        return f"{self.order_number} | {self.user_id} | {self.status}"

    @property
    def subtotal(self):
        """Subtotal before delivery charge."""
        return self.total_amount - self.delivery_charge

    @property
    def is_cancellable(self) -> bool:
        return self.status == OrderStatus.PENDING

    @property
    def is_immutable(self) -> bool:
        return self.status in OrderStatus.IMMUTABLE_STATUSES


# ─── Order Item ───────────────────────────────────────────────────────────────
class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "product.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price snapshot at time of purchase",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        indexes = [
            models.Index(fields=["order"], name="idx_orderitem_order"),
        ]

    def __str__(self):
        return f"OrderItem: {self.order_id} | Product: {self.product_id}"

    @property
    def line_total(self):
        return self.price * self.quantity


# ─── Order Status Log ─────────────────────────────────────────────────────────
class OrderStatusLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_logs",
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_status_changes",
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order"], name="idx_statuslog_order"),
            models.Index(fields=["changed_by"], name="idx_statuslog_admin"),
        ]

    def __str__(self):
        return f"Log: {self.order_id} | {self.old_status} → {self.new_status}"