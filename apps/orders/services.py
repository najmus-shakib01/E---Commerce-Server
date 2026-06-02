import logging
from decimal import Decimal
from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, NotFound

from .models import CartItem, Wishlist, Order, OrderItem, OrderStatusLog
from .constants import (
    OrderStatus,
    DeliveryZone,
    DELIVERY_CHARGE_INSIDE,
    DELIVERY_CHARGE_OUTSIDE,
    ORDER_NUMBER_PREFIX,
)
from .validators import (
    validate_cart_quantity,
    validate_order_status_transition,
    validate_stock_availability,
    validate_product_is_purchasable,
)
from .email_service import send_order_placed_email, send_order_status_email

from django.db.models import QuerySet, F
from apps.product.models import Product

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# INVENTORY SERVICES
# ══════════════════════════════════════════════════════════════════════════════

def validate_stock(product, quantity: int) -> None:
    validate_stock_availability(product, quantity)


def deduct_stock(product, quantity: int) -> None:
    updated = Product.objects.filter(
        id=product.id,
        stock_quantity__gte=quantity,
    ).update(stock_quantity=F("stock_quantity") - quantity)

    if not updated:
        raise ValidationError(
            f"Insufficient stock for '{product.name}'. Please refresh your cart."
        )


def restore_stock(product, quantity: int) -> None:
    Product.objects.filter(id=product.id).update(
        stock_quantity=F("stock_quantity") + quantity
    )


# ══════════════════════════════════════════════════════════════════════════════
# AUDIT SERVICE
# ══════════════════════════════════════════════════════════════════════════════

def create_status_log(order: Order, changed_by, old_status: str, new_status: str) -> OrderStatusLog:
    return OrderStatusLog.objects.create(
        order=order,
        changed_by=changed_by,
        old_status=old_status,
        new_status=new_status,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ORDER NUMBER SERVICE
# ══════════════════════════════════════════════════════════════════════════════

def generate_order_number() -> str:
    year = datetime.now().year
    prefix = f"{ORDER_NUMBER_PREFIX}-{year}-"

    count = Order.objects.filter(order_number__startswith=prefix).count()
    sequence = str(count + 1).zfill(6)
    candidate = f"{prefix}{sequence}"

    while Order.objects.filter(order_number=candidate).exists():
        count += 1
        sequence = str(count + 1).zfill(6)
        candidate = f"{prefix}{sequence}"

    return candidate


# ══════════════════════════════════════════════════════════════════════════════
# DELIVERY CHARGE SERVICE
# ══════════════════════════════════════════════════════════════════════════════

def calculate_delivery_charge(delivery_zone: str) -> Decimal:
    if delivery_zone == DeliveryZone.INSIDE:
        return Decimal(DELIVERY_CHARGE_INSIDE)
    return Decimal(DELIVERY_CHARGE_OUTSIDE)


# ══════════════════════════════════════════════════════════════════════════════
# CART SERVICES
# ══════════════════════════════════════════════════════════════════════════════

def add_to_cart(user, product_id: str, quantity: int) -> CartItem:
    product = get_object_or_404(Product, id=product_id)
    validate_stock_availability(product, quantity)

    cart_item, created = CartItem.objects.get_or_create(
        user=user,
        product=product,
        defaults={"quantity": quantity},
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        validate_cart_quantity(new_quantity, product.stock_quantity)
        cart_item.quantity = new_quantity
        cart_item.save(update_fields=["quantity", "updated_at"])

    logger.info(f"Cart updated: user={user.id}, product={product.id}, qty={cart_item.quantity}")
    return cart_item


def update_cart_quantity(user, cart_item_id: str, quantity: int) -> CartItem:
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=user)
    validate_cart_quantity(quantity, cart_item.product.stock_quantity)

    cart_item.quantity = quantity
    cart_item.save(update_fields=["quantity", "updated_at"])
    return cart_item


def remove_cart_item(user, cart_item_id: str) -> None:
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=user)
    cart_item.delete()
    logger.info(f"Cart item removed: user={user.id}, item={cart_item_id}")


def clear_cart(user) -> None:
    CartItem.objects.filter(user=user).delete()
    logger.info(f"Cart cleared: user={user.id}")


def get_cart_summary(user) -> dict:
    items = CartItem.objects.for_user(user).select_related("product").prefetch_related("product__images")

    subtotal = Decimal("0.00")
    for item in items:
        p = item.product
        unit_price = p.discount_price if p.discount_price else p.regular_price
        subtotal += unit_price * item.quantity

    return {
        "items": items,
        "item_count": items.count(),
        "subtotal": subtotal,
    }


# ══════════════════════════════════════════════════════════════════════════════
# WISHLIST SERVICES
# ══════════════════════════════════════════════════════════════════════════════

def add_to_wishlist(user, product_id: str) -> Wishlist:
    product = get_object_or_404(Product, id=product_id)

    if Wishlist.objects.filter(user=user, product=product).exists():
        raise ValidationError("This product is already in your wishlist.")

    wishlist_item = Wishlist.objects.create(user=user, product=product)
    logger.info(f"Wishlist added: user={user.id}, product={product.id}")
    return wishlist_item


def remove_from_wishlist(user, wishlist_id: str) -> None:
    item = get_object_or_404(Wishlist, id=wishlist_id, user=user)
    item.delete()
    logger.info(f"Wishlist removed: user={user.id}, item={wishlist_id}")


def move_wishlist_to_cart(user, wishlist_id: str) -> CartItem:
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=user)
    product = wishlist_item.product

    validate_stock_availability(product, 1)

    with transaction.atomic():
        cart_item = add_to_cart(user, str(product.id), 1)
        wishlist_item.delete()

    logger.info(f"Wishlist→Cart: user={user.id}, product={product.id}")
    return cart_item


# ══════════════════════════════════════════════════════════════════════════════
# CHECKOUT & ORDER CREATION
# ══════════════════════════════════════════════════════════════════════════════

@transaction.atomic
def create_order(user, shipping_address: str, delivery_zone: str, payment_method: str) -> Order:
    cart_items = list(
        CartItem.objects.filter(user=user).select_related("product")
    )

    if not cart_items:
        raise ValidationError("Your cart is empty. Add items before checkout.")

    subtotal = Decimal("0.00")
    for item in cart_items:
        validate_product_is_purchasable(item.product)
        validate_cart_quantity(item.quantity, item.product.stock_quantity)
        unit_price = (
            item.product.discount_price
            if item.product.discount_price
            else item.product.regular_price
        )
        subtotal += unit_price * item.quantity

    delivery_charge = calculate_delivery_charge(delivery_zone)
    total_amount = subtotal + delivery_charge

    order_number = generate_order_number()

    order = Order.objects.create(
        order_number=order_number,
        user=user,
        total_amount=total_amount,
        shipping_address=shipping_address,
        delivery_charge=delivery_charge,
        status=OrderStatus.PENDING,
        payment_method=payment_method,
    )

    order_items_to_create = []
    for item in cart_items:
        unit_price = (
            item.product.discount_price
            if item.product.discount_price
            else item.product.regular_price
        )
        order_items_to_create.append(
            OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=unit_price,
            )
        )
        updated = Product.objects.filter(
            id=item.product.id,
            stock_quantity__gte=item.quantity,
        ).update(stock_quantity=F("stock_quantity") - item.quantity)

        if not updated:
            raise ValidationError(
                f"Stock for '{item.product.name}' changed during checkout. "
                "Please refresh and try again."
            )

    OrderItem.objects.bulk_create(order_items_to_create)

    CartItem.objects.filter(user=user).delete()

    create_status_log(
        order=order,
        changed_by=user,
        old_status="",
        new_status=OrderStatus.PENDING,
    )

    logger.info(
        f"Order created: {order.order_number} | user={user.id} | total={total_amount}"
    )

    order_with_items = (
        Order.objects.filter(pk=order.pk)
        .select_related("user")
        .prefetch_related("items__product")
        .first()
    )
    send_order_placed_email(order_with_items)

    return order


# ══════════════════════════════════════════════════════════════════════════════
# ORDER MANAGEMENT SERVICES
# ══════════════════════════════════════════════════════════════════════════════

def cancel_order(user, order_number: str) -> Order:

    order = get_object_or_404(Order, order_number=order_number, user=user)

    if not order.is_cancellable:
        raise ValidationError(
            f"Order cannot be cancelled. Current status: '{order.status}'. "
            "Only PENDING orders can be cancelled."
        )

    with transaction.atomic():
        old_status = order.status

        for item in order.items.select_related("product"):
            Product.objects.filter(id=item.product.id).update(
                stock_quantity=F("stock_quantity") + item.quantity
            )

        order.status = OrderStatus.CANCELLED
        order.save(update_fields=["status", "updated_at"])

        create_status_log(
            order=order,
            changed_by=user,
            old_status=old_status,
            new_status=OrderStatus.CANCELLED,
        )

    logger.info(f"Order cancelled: {order.order_number} by user={user.id}")

    order_with_items = (
        Order.objects.filter(pk=order.pk)
        .select_related("user")
        .prefetch_related("items__product")
        .first()
    )
    send_order_status_email(
        order_with_items,
        new_status=OrderStatus.CANCELLED,
        cancellation_note="আপনার অনুরোধে অর্ডারটি বাতিল করা হয়েছে।",
    )

    return order


@transaction.atomic
def update_order_status(admin_user, order_number: str, new_status: str) -> Order:

    order = get_object_or_404(Order, order_number=order_number)

    if order.is_immutable:
        raise ValidationError(
            f"Order '{order_number}' is in a terminal state ({order.status}) and cannot be modified."
        )

    validate_order_status_transition(order.status, new_status)

    old_status = order.status
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    create_status_log(
        order=order,
        changed_by=admin_user,
        old_status=old_status,
        new_status=new_status,
    )

    logger.info(
        f"Order status updated: {order_number} | "
        f"{old_status} → {new_status} by admin={admin_user.id}"
    )
    order_with_items = (
        Order.objects.filter(pk=order.pk)
        .select_related("user")
        .prefetch_related("items__product")
        .first()
    )
    send_order_status_email(order_with_items, new_status=new_status)

    return order


def get_order_details(user, order_number: str) -> Order:
    try:
        return (
            Order.objects.filter(order_number=order_number, user=user)
            .select_related("user")
            .prefetch_related(
                "items__product",
                "status_logs__changed_by",
            )
            .get()
        )
    except Order.DoesNotExist:
        raise NotFound(f"Order '{order_number}' not found.")


def list_user_orders(user) -> QuerySet:
    return (
        Order.objects.filter(user=user)
        .prefetch_related("items")
        .order_by("-created_at")
    )