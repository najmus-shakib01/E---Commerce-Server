from django.contrib import admin
from django.utils.html import format_html
from .models import CartItem, Wishlist, Order, OrderItem, OrderStatusLog

# ─── Cart Item Admin ──────────────────────────────────────────────────────────
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "quantity", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__email", "product__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["user", "product"]


# ─── Wishlist Admin ───────────────────────────────────────────────────────────
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "product", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__email", "product__name"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["user", "product"]


# ─── Order Item Inline ────────────────────────────────────────────────────────
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["id", "product", "quantity", "price", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


# ─── Order Status Log Inline ──────────────────────────────────────────────────
class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ["id", "changed_by", "old_status", "new_status", "created_at"]
    can_delete = False
    ordering = ["-created_at"]

    def has_add_permission(self, request, obj=None):
        return False


# ─── Order Admin ──────────────────────────────────────────────────────────────
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "user",
        "status_badge",
        "payment_method",
        "total_amount",
        "delivery_charge",
        "courier_name",
        "tracking_id",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "created_at"]
    search_fields = ["order_number", "user__email", "tracking_id"]
    readonly_fields = [
        "id",
        "order_number",
        "user",
        "total_amount",
        "delivery_charge",
        "payment_method",
        "created_at",
        "updated_at",
    ]
    inlines = [OrderItemInline, OrderStatusLogInline]
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .prefetch_related("items", "status_logs")
        )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "PENDING": "#f59e0b",
            "CONFIRMED": "#3b82f6",
            "SHIPPED": "#8b5cf6",
            "DELIVERED": "#10b981",
            "CANCELLED": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;">{}</span>',
            color,
            obj.get_status_display(),
        )


# ─── Order Status Log Admin ───────────────────────────────────────────────────
@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ["order", "old_status", "new_status", "changed_by", "created_at"]
    list_filter = ["new_status", "created_at"]
    search_fields = ["order__order_number", "changed_by__email"]
    readonly_fields = ["id", "order", "changed_by", "old_status", "new_status", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False