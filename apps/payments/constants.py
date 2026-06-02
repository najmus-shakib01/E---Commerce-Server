class PaymentStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]


class ReviewRating:
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

    CHOICES = [
        (ONE,   "★☆☆☆☆ — Very Poor"),
        (TWO,   "★★☆☆☆ — Poor"),
        (THREE, "★★★☆☆ — Average"),
        (FOUR,  "★★★★☆ — Good"),
        (FIVE,  "★★★★★ — Excellent"),
    ]

    MIN = ONE
    MAX = FIVE


class ImageConstants:
    MAX_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB
    ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
    ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]