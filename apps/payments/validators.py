import os
from django.core.exceptions import ValidationError
from apps.payments.constants import ImageConstants, ReviewRating

def validate_image_file(image) -> None:
    if not image:
        return

    if image.size > ImageConstants.MAX_SIZE_BYTES:
        raise ValidationError("Image size must not exceed 1MB.")

    ext = os.path.splitext(image.name)[1].lstrip(".").lower()
    if ext not in ImageConstants.ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported image format. Allowed: {', '.join(ImageConstants.ALLOWED_EXTENSIONS)}"
        )

def validate_transaction_id(transaction_id: str) -> None:
    if not transaction_id or not transaction_id.strip():
        raise ValidationError("Transaction ID cannot be empty.")

    if len(transaction_id.strip()) < 6:
        raise ValidationError("Transaction ID must be at least 6 characters.")


def validate_payment_screenshot(screenshot) -> None:
    if not screenshot:
        raise ValidationError("Payment screenshot is required.")
    validate_image_file(screenshot)


def validate_review_rating(rating: int) -> None:
    if not isinstance(rating, int) or not (
        ReviewRating.MIN <= rating <= ReviewRating.MAX
    ):
        raise ValidationError(
            f"Rating must be between {ReviewRating.MIN} and {ReviewRating.MAX} stars."
        )

def validate_review_image(image) -> None:
    if image:
        validate_image_file(image)