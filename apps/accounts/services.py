import json
import logging
import os
import random
import string
import urllib.parse
import urllib.request
from datetime import timedelta
from typing import Dict, Any
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from google.auth.transport.requests import Request
from google.oauth2 import id_token as google_id_token
from rest_framework import serializers as drf_serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .constants import (
    OTP_EXPIRE_SECONDS,
    OTP_MAX_RESEND,
    OTP_MAX_RETRY,
    OTP_RESEND_COOLDOWN_SECONDS,
    AuthProvider,
    UserRole,
)
from .models import OTPVerification, User, UserProfile
from .validators import validate_password_strength
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))

def _get_tokens_for_user(user: User) -> Dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def _send_otp_email(email: str, otp: str) -> None:
    subject = "Your OTP Verification Code – Shaistaganj E-shop"
    html_message = render_to_string(
        "otp_email.html",
        {"otp": otp, "expiry_minutes": OTP_EXPIRE_SECONDS // 60},
    )
    send_mail(
        subject=subject,
        message=f"Your OTP is {otp}. It expires in {OTP_EXPIRE_SECONDS // 60} minute(s).",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )

def _user_info(user: User) -> Dict[str, Any]:
    profile = getattr(user, "profile", None)
    image_url = None
    if profile and profile.image:
        try:
            image_url = profile.image.url
        except Exception:
            image_url = None
    
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "full_name": profile.full_name if profile else "",
        "image": image_url,
    }

# ---------------------------------------------------------------------------
# 1. Register
# ---------------------------------------------------------------------------

@transaction.atomic
def register_user(email: str, password: str) -> Dict[str, Any]:
    email = email.lower().strip()

    if User.objects.filter(email=email, deleted_at__isnull=True).exists():
        raise drf_serializers.ValidationError(
            {"email": "A user with this email already exists."}
        )

    try:
        validate_password_strength(password)
    except Exception as exc:
        raise drf_serializers.ValidationError({"password": str(exc)})

    user = User.objects.create_user(
        email=email,
        password=password,
        is_active=False,
        auth_provider=AuthProvider.EMAIL,
    )

    otp = _generate_otp()
    expire_at = timezone.now() + timedelta(seconds=OTP_EXPIRE_SECONDS)
    OTPVerification.objects.filter(email=email, is_used=False).update(is_used=True)

    OTPVerification.objects.create(
        email=email,
        otp_code=otp,
        expire_at=expire_at,
    )

    _send_otp_email(email, otp)
    logger.info("New user registered: %s", email)

    return {"email": user.email}


# ---------------------------------------------------------------------------
# 2. Verify OTP
# ---------------------------------------------------------------------------

@transaction.atomic
def verify_otp(email: str, otp_input: str) -> Dict[str, Any]:
    email = email.lower().strip()

    otp_obj = (
        OTPVerification.objects.filter(email=email, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if not otp_obj:
        raise drf_serializers.ValidationError({"otp": "No active OTP found for this email."})

    if otp_obj.is_expired():
        raise drf_serializers.ValidationError({"otp": "OTP has expired. Please request a new one."})

    if otp_obj.is_max_retry_reached():
        raise drf_serializers.ValidationError(
            {"otp": "Maximum retry attempts reached. Please request a new OTP."}
        )

    if otp_obj.otp_code != otp_input:
        otp_obj.retry_count += 1
        otp_obj.save(update_fields=["retry_count"])
        remaining = OTP_MAX_RETRY - otp_obj.retry_count
        raise drf_serializers.ValidationError(
            {"otp": f"Invalid OTP. {remaining} attempt(s) remaining."}
        )

    otp_obj.is_used = True
    otp_obj.save(update_fields=["is_used"])

    try:
        user = User.objects.get(email=email, deleted_at__isnull=True)
    except User.DoesNotExist:
        raise drf_serializers.ValidationError({"email": "User not found."})

    user.is_active = True
    user.save(update_fields=["is_active"])

    logger.info("OTP verified for: %s", email)
    return {"email": email, "verified": True}


# ---------------------------------------------------------------------------
# 3. Resend OTP
# ---------------------------------------------------------------------------

@transaction.atomic
def resend_otp(email: str) -> Dict[str, Any]:
    email = email.lower().strip()

    try:
        user = User.objects.get(email=email, deleted_at__isnull=True)
    except User.DoesNotExist:
        raise drf_serializers.ValidationError({"email": "User not found."})

    if user.is_active:
        raise drf_serializers.ValidationError({"email": "User is already verified."})

    otp_obj = (
        OTPVerification.objects.filter(email=email, is_used=False)
        .order_by("-created_at")
        .first()
    )

    if otp_obj and otp_obj.resend_count >= OTP_MAX_RESEND:
        if otp_obj.last_resend_at:
            elapsed = (timezone.now() - otp_obj.last_resend_at).total_seconds()
            if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                wait = int((OTP_RESEND_COOLDOWN_SECONDS - elapsed) / 60)
                raise drf_serializers.ValidationError(
                    {"otp": f"Maximum resend limit reached. Try again in {wait} minute(s)."}
                )

    OTPVerification.objects.filter(email=email, is_used=False).update(is_used=True)

    new_otp = _generate_otp()
    resend_count = (otp_obj.resend_count + 1) if otp_obj else 1

    OTPVerification.objects.create(
        email=email,
        otp_code=new_otp,
        expire_at=timezone.now() + timedelta(seconds=OTP_EXPIRE_SECONDS),
        resend_count=resend_count,
        last_resend_at=timezone.now(),
    )

    _send_otp_email(email, new_otp)
    logger.info("OTP resent to: %s (resend #%d)", email, resend_count)

    return {"email": email, "resend_count": resend_count}


# ---------------------------------------------------------------------------
# 4. Login
# ---------------------------------------------------------------------------

def login_user(email: str, password: str, request=None) -> Dict[str, Any]:
    email = email.lower().strip()

    user = authenticate(request=request, username=email, password=password)

    if user is None:
        try:
            db_user = User.objects.get(email=email, deleted_at__isnull=True)
            if not db_user.is_active:
                raise drf_serializers.ValidationError(
                    {"email": "Account is not verified. Please verify your OTP."}
                )
        except User.DoesNotExist:
            pass
        raise drf_serializers.ValidationError(
            {"non_field_errors": "Invalid email or password."}
        )

    if not user.is_active:
        raise drf_serializers.ValidationError(
            {"email": "Account is not verified. Please verify your OTP."}
        )
    if user.is_banned:
        raise drf_serializers.ValidationError(
            {"email": f"Account is banned. Reason: {user.banned_reason}"}
        )
    if not user.is_enabled:
        raise drf_serializers.ValidationError(
            {"email": "Account is disabled. Contact support."}
        )
    if user.deleted_at is not None:
        raise drf_serializers.ValidationError(
            {"email": "Account not found."}
        )

    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])

    tokens = _get_tokens_for_user(user)
    logger.info("User logged in: %s", email)

    return {
        "tokens": tokens,
        "user": _user_info(user),
    }


# ---------------------------------------------------------------------------
# 5. Logout
# ---------------------------------------------------------------------------

def logout_user(refresh_token: str) -> None:
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        logger.info("Refresh token blacklisted.")
    except Exception:
        raise drf_serializers.ValidationError(
            {"refresh": "Invalid or already blacklisted token."}
        )


# ---------------------------------------------------------------------------
# 6. Forgot Password
# ---------------------------------------------------------------------------

def forgot_password(email: str) -> None:
    email = email.lower().strip()

    try:
        user = User.objects.get(
            email=email,
            is_active=True,
            deleted_at__isnull=True,
        )
    except User.DoesNotExist:
        logger.info("Password reset requested for non-existent email: %s", email)
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)

    reset_link = (
        f"{settings.FRONTEND_BASE_URL}/reset-password/{uid}/{token}/"
    )

    html_message = render_to_string(
        "password_reset_email.html",
        {
            "reset_link": reset_link,
            "expiry_minutes": settings.PASSWORD_RESET_EXPIRY_MINUTES,
            "user_email": email,
        },
    )

    send_mail(
        subject="Password Reset Request – Shaistaganj E-shop",
        message=f"Reset your password: {reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )
    logger.info("Password reset email sent to: %s", email)


# ---------------------------------------------------------------------------
# 7. Reset Password
# ---------------------------------------------------------------------------

@transaction.atomic
def reset_password(uid: str, token: str, new_password: str) -> None:
    try:
        user_pk = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_pk, deleted_at__isnull=True)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        raise drf_serializers.ValidationError({"uid": "Invalid reset link."})

    token_generator = PasswordResetTokenGenerator()
    if not token_generator.check_token(user, token):
        raise drf_serializers.ValidationError(
            {"token": "Reset link is invalid or has expired."}
        )

    try:
        validate_password_strength(new_password)
    except Exception as exc:
        raise drf_serializers.ValidationError({"password": str(exc)})

    user.set_password(new_password)
    user.save(update_fields=["password"])
    logger.info("Password reset successful for: %s", user.email)


# ---------------------------------------------------------------------------
# 8. Update Profile
# ---------------------------------------------------------------------------

@transaction.atomic
def update_profile(user: User, validated_data: Dict[str, Any]) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)

    allowed_fields = ["full_name", "phone", "image", "gender", "address", "date_of_birth"]

    if "image" in validated_data:
        old_image = profile.image
        new_image = validated_data["image"]
        profile.image = new_image
        profile.save(update_fields=["image"])

        if old_image and old_image != new_image:
            try:
                if old_image.path and os.path.exists(old_image.path):
                    os.remove(old_image.path)
                else:
                    logger.warning(f"Old image file not found: {old_image.path}")
            except Exception as e:
                logger.warning(f"Could not delete old image: {e}")
    
    for field in allowed_fields:
        if field in validated_data and field != "image":
            setattr(profile, field, validated_data[field])

    profile.full_clean()
    profile.save()
    logger.info("Profile updated for: %s", user.email)
    return profile

# ---------------------------------------------------------------------------
# 9. Google OAuth
# ---------------------------------------------------------------------------

def google_auth_code_exchange(code: str) -> str:
    token_endpoint = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    data = urllib.parse.urlencode(payload).encode('utf-8')
    req = urllib.request.Request(token_endpoint, data=data)
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode())
            return response_data.get("id_token")
    except urllib.error.URLError as e:
        logger.error("Failed to exchange auth code: %s", e)
        raise drf_serializers.ValidationError({"code": "Failed to exchange auth code with Google."})

@transaction.atomic
def google_authenticate(id_token_str: str) -> Dict[str, Any]:
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token_str,
            Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        logger.error("Google OAuth ValueError: %s", exc)
        raise drf_serializers.ValidationError(
            {"id_token": f"Invalid Google token: {exc}"}
        )
    except Exception as exc:
        logger.error("Google OAuth Exception: %s", exc)
        raise drf_serializers.ValidationError(
            {"id_token": f"Google authentication failed: {exc}"}
        )

    email = id_info.get("email", "").lower().strip()
    if not email:
        raise drf_serializers.ValidationError({"token": "Google token missing email."})

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "auth_provider": AuthProvider.GOOGLE,
            "is_active": True,
            "role": UserRole.USER,
        },
    )

    if not created:
        if user.auth_provider != AuthProvider.GOOGLE:
            user.auth_provider = AuthProvider.GOOGLE
            user.save(update_fields=["auth_provider"])
        
        if user.deleted_at is not None:
            raise drf_serializers.ValidationError(
                {"email": "Account not found."}
            )

    if user.is_banned:
        raise drf_serializers.ValidationError(
            {"email": f"Account is banned. Reason: {user.banned_reason}"}
        )
    if not user.is_enabled:
        raise drf_serializers.ValidationError({"email": "Account is disabled."})

    profile, profile_created = UserProfile.objects.get_or_create(user=user)
    
    if profile_created or not profile.full_name:
        profile.full_name = id_info.get("name", "")
        profile.save(update_fields=["full_name"])

    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])

    tokens = _get_tokens_for_user(user)
    logger.info("Google OAuth login: %s (new=%s, profile_created=%s)", email, created, profile_created)

    return {
        "tokens": tokens,
        "user": _user_info(user),
        "is_new_user": created,
    }