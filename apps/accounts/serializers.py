from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import UserProfile
from .validators import (
    validate_password_strength,
)

# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_password(self, value: str) -> str:
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


# ---------------------------------------------------------------------------
# OTP
# ---------------------------------------------------------------------------

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class OTPResendSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


# ---------------------------------------------------------------------------
# Forgot / Reset Password
# ---------------------------------------------------------------------------

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_password(self, value: str) -> str:
        try:
            validate_password_strength(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

from rest_framework.validators import UniqueValidator

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    image = serializers.SerializerMethodField()
    image_upload = serializers.ImageField(
        write_only=True, required=False, source="image"
    )
    phone = serializers.CharField(
        max_length=11,
        required=False,
        allow_null=True,
        allow_blank=True,
        validators=[
            UniqueValidator(
                queryset=UserProfile.objects.all(),
                message="This phone number is already in use."
            )
        ]
    )

    class Meta:
        model = UserProfile
        fields = [
            "email", "role", "full_name", "phone",
            "image", "image_upload",
            "gender", "address", "date_of_birth",
        ]

    def get_image(self, obj):
        if obj and obj.image:
            try:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
            except Exception:
                return None
        return None

    def update(self, instance, validated_data):
        image = validated_data.pop("image", None)
        if image:
            if instance.image:
                try:
                    import os
                    if os.path.exists(instance.image.path):
                        os.remove(instance.image.path)
                except Exception:
                    pass
            instance.image = image

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
    
# ---------------------------------------------------------------------------
# Google Auth
# ---------------------------------------------------------------------------

class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()