import os
from django.core.exceptions import ValidationError
from .constants import (
    MAX_IMAGE_SIZE_BYTES,
    MAX_IMAGE_SIZE_MB,
    ALLOWED_IMAGE_EXTENSIONS,
)

def validate_image_size(image) -> None:

    if image and hasattr(image, "size"):
        if image.size > MAX_IMAGE_SIZE_BYTES:
            raise ValidationError(
                f"Image size must not exceed {MAX_IMAGE_SIZE_MB}MB. "
                f"Uploaded file size: {image.size / (1024 * 1024):.2f}MB."
            )


def validate_image_extension(image) -> None:
    if image and hasattr(image, "name"):
        ext = os.path.splitext(image.name)[1].lstrip(".").lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                f"Unsupported image format '{ext}'. "
                f"Allowed formats: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
            )


def validate_discount_price(discount_price, regular_price) -> None:
    if discount_price is not None and regular_price is not None:
        if discount_price >= regular_price:
            raise ValidationError(
                "Discount price must be strictly less than the regular price."
            )
        if discount_price < 0:
            raise ValidationError("Discount price cannot be negative.")


def validate_stock_quantity(stock_quantity) -> None:
    if stock_quantity is not None and stock_quantity < 0:
        raise ValidationError("Stock quantity cannot be negative.")


def validate_image_file(image) -> None:
    validate_image_extension(image)
    validate_image_size(image)