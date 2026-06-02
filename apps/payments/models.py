from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from apps.payments.constants import PaymentStatus
from apps.payments.managers import ManualPaymentManager, ReviewManager
from apps.payments.validators import (
    validate_payment_screenshot,
    validate_review_image,
)
from apps.payments.constants import ReviewRating

class ManualPayment(models.Model):

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="manual_payment",
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    screenshot = models.ImageField(
        upload_to="payments/",
        validators=[validate_payment_screenshot],
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.CHOICES,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ManualPaymentManager()

    class Meta:
        db_table = "payments_manual"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["status"]),
        ]
        verbose_name = "Manual Payment"
        verbose_name_plural = "Manual Payments"

    def __str__(self):
        return f"Payment [{self.transaction_id}] - {self.status}"

    @property
    def is_pending(self) -> bool:
        return self.status == PaymentStatus.PENDING

    @property
    def is_approved(self) -> bool:
        return self.status == PaymentStatus.APPROVED


class Review(models.Model):

    product = models.ForeignKey(
        "product.Product",
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        db_index=True,
    )
    rating = models.PositiveSmallIntegerField(
        choices=ReviewRating.CHOICES,
        validators=[
            MinValueValidator(ReviewRating.MIN),
            MaxValueValidator(ReviewRating.MAX),
        ],
    )
    comment = models.TextField()
    image = models.ImageField(
        upload_to="reviews/",
        null=True,
        blank=True,
        validators=[validate_review_image],
    )
    is_approved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ReviewManager()

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_review_per_user_per_product",
            )
        ]
        indexes = [
            models.Index(fields=["product", "is_approved"]),
            models.Index(fields=["user"]),
        ]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f"Review by {self.user_id} on product {self.product_id} - {self.rating}★"