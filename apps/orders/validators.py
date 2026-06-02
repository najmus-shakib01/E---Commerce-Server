from rest_framework.exceptions import ValidationError
from .constants import (
    OrderStatus,
    CART_MIN_QUANTITY,
    CART_MAX_QUANTITY_PER_ITEM,
)

def validate_cart_quantity(quantity: int, available_stock: int) -> None:
    """
    Validate that the requested cart quantity is within acceptable bounds.

    Raises:
        ValidationError: if quantity < min, > max, or exceeds stock.
    """
    if quantity < CART_MIN_QUANTITY:
        raise ValidationError(
            f"Quantity must be at least {CART_MIN_QUANTITY}."
        )

    if quantity > CART_MAX_QUANTITY_PER_ITEM:
        raise ValidationError(
            f"Quantity cannot exceed {CART_MAX_QUANTITY_PER_ITEM} per item."
        )

    if quantity > available_stock:
        raise ValidationError(
            f"Requested quantity ({quantity}) exceeds available stock ({available_stock})."
        )

def validate_order_status_transition(current_status: str, new_status: str) -> None:
    """
    Validate that the requested order status transition is allowed.

    Raises:
        ValidationError: if the transition is not permitted.
    """
    allowed = OrderStatus.ALLOWED_TRANSITIONS.get(current_status, [])

    if new_status not in allowed:
        raise ValidationError(
            f"Cannot transition order from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {allowed if allowed else 'none (terminal state)'}."
        )


def validate_stock_availability(product, quantity: int) -> None:
    """
    Validate that a product is active, in stock, and has enough quantity.

    Args:
        product: Product model instance.
        quantity: Requested quantity.

    Raises:
        ValidationError: on any stock/active violation.
    """
    if not product.is_active:
        raise ValidationError(
            f"Product '{product.name}' is currently unavailable."
        )

    if product.stock_quantity <= 0:
        raise ValidationError(
            f"Product '{product.name}' is out of stock."
        )

    if quantity > product.stock_quantity:
        raise ValidationError(
            f"Only {product.stock_quantity} unit(s) of '{product.name}' available."
        )


def validate_product_is_purchasable(product) -> None:
    """
    Lightweight check — product must be active and have stock > 0.
    Used during checkout validation loop.
    """
    if not product.is_active:
        raise ValidationError(
            f"Product '{product.name}' is no longer available for purchase."
        )
    if product.stock_quantity <= 0:
        raise ValidationError(
            f"Product '{product.name}' went out of stock. Please remove it from your cart."
        )