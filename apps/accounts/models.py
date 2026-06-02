import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .constants import AuthProvider, GenderChoice, UserRole
from .managers import UserManager
from .validators import (
    validate_bd_phone,
    validate_image_extension,
    validate_image_size,
)

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin, TimestampMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
    )
    auth_provider = models.CharField(
        max_length=10,
        choices=AuthProvider.choices,
        default=AuthProvider.EMAIL,
    )

    # Account status flags
    is_active = models.BooleanField(default=False)   
    is_enabled = models.BooleanField(default=True)  
    is_staff = models.BooleanField(default=False)    

    # Ban info
    is_banned = models.BooleanField(default=False)
    banned_at = models.DateTimeField(null=True, blank=True)
    banned_reason = models.TextField(null=True, blank=True)
    banned_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="banned_users",
    )

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_users",
    )

    last_login_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_active", "is_enabled", "is_banned"]),
            models.Index(fields=["deleted_at"]),
        ]

    def __str__(self):
        return self.email

    # ------------------------------------------------------------------
    # Soft delete helpers
    # ------------------------------------------------------------------
    def soft_delete(self, deleted_by_user=None):
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by_user
        self.is_active = False
        self.save(update_fields=["deleted_at", "deleted_by", "is_active"])

    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    # ------------------------------------------------------------------
    # Ban helpers
    # ------------------------------------------------------------------
    def ban(self, reason: str, banned_by_user=None):
        self.is_banned = True
        self.banned_at = timezone.now()
        self.banned_reason = reason
        self.banned_by = banned_by_user
        self.save(update_fields=["is_banned", "banned_at", "banned_reason", "banned_by"])

    def unban(self):
        self.is_banned = False
        self.banned_at = None
        self.banned_reason = None
        self.banned_by = None
        self.save(update_fields=["is_banned", "banned_at", "banned_reason", "banned_by"])


class UserProfile(TimestampMixin):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_bd_phone],
    )
    image = models.ImageField(
        upload_to="profiles/",
        null=True,
        blank=True,
        validators=[validate_image_size, validate_image_extension],
    )
    gender = models.CharField(
        max_length=10,
        choices=GenderChoice.choices,
        null=True,
        blank=True,
    )
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"Profile – {self.user.email}"


class OTPVerification(models.Model):
    email = models.EmailField(db_index=True)
    otp_code = models.CharField(max_length=6)
    expire_at = models.DateTimeField()
    retry_count = models.PositiveSmallIntegerField(default=0)
    resend_count = models.PositiveSmallIntegerField(default=0)
    last_resend_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_verifications"
        indexes = [models.Index(fields=["email", "is_used"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.email}"

    def is_expired(self) -> bool:
        return timezone.now() > self.expire_at

    def is_max_retry_reached(self) -> bool:
        from .constants import OTP_MAX_RETRY
        return self.retry_count >= OTP_MAX_RETRY