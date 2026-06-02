import os
import re
from django.core.exceptions import ValidationError

def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/`~';]", password):
        raise ValidationError("Password must contain at least one special character.")


def validate_bd_phone(phone: str) -> None:
    if not re.fullmatch(r"01[3-9]\d{8}", phone):
        raise ValidationError(
            "Enter a valid Bangladesh phone number (e.g. 01XXXXXXXXX)."
        )


def validate_image_size(image) -> None:
    max_size = 1 * 1024 * 1024  
    if image.size > max_size:
        raise ValidationError("Image size must not exceed 1 MB.")


def validate_image_extension(image) -> None:
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in allowed:
        raise ValidationError(
            f"Unsupported image format '{ext}'. "
            f"Allowed formats: {', '.join(allowed)}"
        )