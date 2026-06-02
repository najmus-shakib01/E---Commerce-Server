from django.db import models

class VariantType(models.TextChoices):
    SIZE = "SIZE", "Size"
    COLOR = "COLOR", "Color"


class SortOption:
    LOW_TO_HIGH = "low_to_high"
    HIGH_TO_LOW = "high_to_low"
    NEWEST = "newest"
    OLDEST = "oldest"
    POPULAR = "popular"

    CHOICES = [
        (LOW_TO_HIGH, "Price: Low to High"),
        (HIGH_TO_LOW, "Price: High to Low"),
        (NEWEST, "Newest First"),
        (OLDEST, "Oldest First"),
        (POPULAR, "Most Popular"),
    ]


# Image validation
MAX_IMAGE_SIZE_MB = 1
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
ALLOWED_IMAGE_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]

# Related products
RELATED_PRODUCTS_LIMIT = 8

# Pagination
DEFAULT_PAGE_SIZE = 20