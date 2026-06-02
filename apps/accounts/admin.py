from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import OTPVerification, User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = ["full_name", "phone", "image", "gender", "address", "date_of_birth"]
    readonly_fields = []
    extra = 0

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "full_name", "image", "phone"]

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = [
        "email", "role", "auth_provider",
        "is_active", "is_enabled", "is_banned",
        "last_login_at", "created_at",
    ]
    list_filter = ["role", "auth_provider", "is_active", "is_enabled", "is_banned"]
    search_fields = ["email"]
    readonly_fields = [
        "id", "last_login_at", "created_at", "updated_at",
        "banned_at", "banned_by", "deleted_at", "deleted_by",
    ]
    ordering = ["-created_at"]
    fieldsets = (
        ("Credentials", {"fields": ("id", "email", "password")}),
        ("Role & Provider", {"fields": ("role", "auth_provider")}),
        ("Status", {"fields": ("is_active", "is_enabled", "is_staff", "is_superuser")}),
        ("Ban Info", {"fields": ("is_banned", "banned_at", "banned_reason", "banned_by")}),
        ("Soft Delete", {"fields": ("deleted_at", "deleted_by")}),
        ("Timestamps", {"fields": ("last_login_at", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_active"),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("profile")


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = [
        "email", "otp_code", "expire_at",
        "retry_count", "resend_count", "is_used", "created_at",
    ]
    list_filter = ["is_used"]
    search_fields = ["email"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]