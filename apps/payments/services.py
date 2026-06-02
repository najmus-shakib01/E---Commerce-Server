import logging
from typing import Any
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
from apps.payments.models import ManualPayment, Review
from apps.payments.constants import PaymentStatus
from apps.payments.serializers import (
    ManualPaymentSerializer,
    PaymentDetailSerializer,
    ReviewSerializer,
    ReviewModerationSerializer,
    ReviewUpdateSerializer,
)
User = get_user_model()
logger = logging.getLogger(__name__)
from apps.orders.models import Order, OrderItem

# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def validate_purchase_history(user, product_id: int) -> None:

    delivered = (
        Order.objects.filter(
            user=user,
            status="DELIVERED",
        )
        .prefetch_related("items")
        .values_list("id", flat=True)
    )

    has_purchased = OrderItem.objects.filter(
        order_id__in=delivered,
        product_id=product_id,
    ).exists()

    if not has_purchased:
        raise PermissionDenied(
            "You can only review products you have purchased and received."
        )


def validate_review_permission(user, review: Review) -> None:
    """Ensure the user owns the review."""
    if review.user_id != user.id:
        raise PermissionDenied("You do not have permission to modify this review.")


# ─────────────────────────────────────────────────────────────────────────────
# PAYMENT SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def submit_manual_payment(user, data: dict) -> dict:
    from apps.orders.models import Order
    from decimal import Decimal

    order_id = data.get("order").id if hasattr(data.get("order"), "id") else data.get("order")

    try:
        order = Order.objects.get(id=order_id, user=user)
    except Order.DoesNotExist:
        raise NotFound("Order not found or does not belong to you.")

    if order.status != "PENDING":
        raise ValidationError({"detail": f"You can only submit payment for pending orders. Current order status: {order.status}."})

    if order.payment_method != "MANUAL_MFS":
        raise ValidationError({"detail": "This order does not use manual payment."})

    if ManualPayment.objects.filter(order=order).exists():
        raise ValidationError({"detail": "A payment for this order already exists."})

    submitted_amount = data.get("amount")
    if submitted_amount is not None:
        try:
            if abs(Decimal(str(submitted_amount)) - order.total_amount) > Decimal("0.01"):
                raise ValidationError({"amount": f"Submitted payment amount ({submitted_amount}) does not match the order total ({order.total_amount})."})
        except (ValueError, TypeError, ArithmeticError):
            raise ValidationError({"amount": "Invalid amount submitted."})

    serializer = ManualPaymentSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        payment = serializer.save()

    logger.info(f"Manual payment submitted: order={order_id}, txn={payment.transaction_id}")
    return PaymentDetailSerializer(payment).data


def get_payment_details(user, payment_id: int) -> dict:
    try:
        payment = (
            ManualPayment.objects
            .with_relations()
            .get(id=payment_id)
        )
    except ManualPayment.DoesNotExist:
        raise NotFound("Payment not found.")

    if not user.is_staff and payment.order.user_id != user.id:
        raise PermissionDenied("You cannot view this payment.")

    return PaymentDetailSerializer(payment).data


@transaction.atomic
def approve_payment(admin_user, payment_id: int) -> dict:
    try:
        payment = (
            ManualPayment.objects
            .select_related("order")
            .select_for_update()
            .get(id=payment_id)
        )
    except ManualPayment.DoesNotExist:
        raise NotFound("Payment not found.")

    if not payment.is_pending:
        raise ValidationError({"detail": f"Payment is already {payment.status}."})

    order = payment.order
    if order.status != "PENDING":
        raise ValidationError({"detail": f"Cannot approve payment. Order status is not PENDING (current status: {order.status})."})

    payment.status = PaymentStatus.APPROVED
    payment.verified_by = admin_user
    payment.save(update_fields=["status", "verified_by", "updated_at"])

    order.status = "CONFIRMED"
    order.save(update_fields=["status", "updated_at"])

    logger.info(
        f"Payment approved: id={payment_id}, order={order.id}, by={admin_user.email}"
    )
    return PaymentDetailSerializer(payment).data


@transaction.atomic
def reject_payment(admin_user, payment_id: int) -> dict:
    try:
        payment = (
            ManualPayment.objects
            .select_related("order")
            .select_for_update()
            .get(id=payment_id)
        )
    except ManualPayment.DoesNotExist:
        raise NotFound("Payment not found.")

    if not payment.is_pending:
        raise ValidationError({"detail": f"Payment is already {payment.status}."})

    payment.status = PaymentStatus.REJECTED
    payment.verified_by = admin_user
    payment.save(update_fields=["status", "verified_by", "updated_at"])

    logger.info(
        f"Payment rejected: id={payment_id}, order={payment.order_id}, by={admin_user.email}"
    )
    return PaymentDetailSerializer(payment).data


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW SERVICES
# ─────────────────────────────────────────────────────────────────────────────

def create_review(user, data: dict) -> dict:
    product_id = data.get("product").id if hasattr(data.get("product"), "id") else data.get("product")

    validate_purchase_history(user, product_id)

    if Review.objects.filter(user=user, product_id=product_id).exists():
        raise ValidationError({"detail": "You have already reviewed this product."})

    serializer = ReviewSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        review = serializer.save(user=user, is_approved=False)

    logger.info(f"Review created: user={user.id}, product={product_id}")
    return ReviewSerializer(review).data


def update_review(user, review_id: int, data: dict) -> dict:
    """User updates their own review (resets approval)."""
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        raise NotFound("Review not found.")

    validate_review_permission(user, review)

    serializer = ReviewUpdateSerializer(review, data=data, partial=True)
    serializer.is_valid(raise_exception=True)

    with transaction.atomic():
        review = serializer.save(is_approved=False) 

    logger.info(f"Review updated: id={review_id}, user={user.id}")
    return ReviewSerializer(review).data


def delete_review(user, review_id: int) -> None:
    """User deletes their own review."""
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        raise NotFound("Review not found.")

    validate_review_permission(user, review)

    review.delete()
    logger.info(f"Review deleted: id={review_id}, user={user.id}")


def approve_review(admin_user, review_id: int) -> dict:
    """Admin approves a review — makes it publicly visible."""
    try:
        review = Review.objects.with_relations().get(id=review_id)
    except Review.DoesNotExist:
        raise NotFound("Review not found.")

    review.is_approved = True
    review.save(update_fields=["is_approved", "updated_at"])

    logger.info(f"Review approved: id={review_id}, by={admin_user.email}")
    return ReviewModerationSerializer(review).data


def reject_review(admin_user, review_id: int) -> dict:
    """Admin rejects a review — hides it from public."""
    try:
        review = Review.objects.with_relations().get(id=review_id)
    except Review.DoesNotExist:
        raise NotFound("Review not found.")

    review.is_approved = False
    review.save(update_fields=["is_approved", "updated_at"])

    logger.info(f"Review rejected: id={review_id}, by={admin_user.email}")
    return ReviewModerationSerializer(review).data


def list_product_reviews(product_id: int, filterset=None) -> Any:
    from apps.product.models import Product

    if not Product.objects.filter(id=product_id, is_active=True).exists():
        raise NotFound("Product not found.")

    qs = (
        Review.objects
        .approved()
        .for_product(product_id)
        .with_relations()
    )

    if filterset is not None:
        qs = filterset(qs)

    return qs