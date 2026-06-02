# ─── Order Status ──────────────────────────────────────────────────────────────
class OrderStatus:
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

    CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (SHIPPED, "Shipped"),
        (DELIVERED, "Delivered"),
        (CANCELLED, "Cancelled"),
    ]

    ALLOWED_TRANSITIONS: dict = {
        PENDING: [CONFIRMED, CANCELLED],
        CONFIRMED: [SHIPPED],
        SHIPPED: [DELIVERED],
        DELIVERED: [],
        CANCELLED: [],
    }

    IMMUTABLE_STATUSES = [DELIVERED, CANCELLED]


# ─── Payment Method ────────────────────────────────────────────────────────────
class PaymentMethod:
    COD = "COD"
    MANUAL_MFS = "MANUAL_MFS"

    CHOICES = [
        (COD, "Cash on Delivery"),
        (MANUAL_MFS, "Manual Mobile Banking / Bank"),
    ]


# ─── Delivery Charge ──────────────────────────────────────────────────────────
class DeliveryZone:
    INSIDE = "inside"
    OUTSIDE = "outside"

    CHOICES = [
        (INSIDE, "Shaistaganj (Inside)"),
        (OUTSIDE, "Outside Shaistaganj"),
    ]


DELIVERY_CHARGE_INSIDE: int = 60      
DELIVERY_CHARGE_OUTSIDE: int = 120    


# ─── Order Number ─────────────────────────────────────────────────────────────
ORDER_NUMBER_PREFIX = "ORD"

# ─── Cart ─────────────────────────────────────────────────────────────────────
CART_MAX_QUANTITY_PER_ITEM: int = 100
CART_MIN_QUANTITY: int = 1