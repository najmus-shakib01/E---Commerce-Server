from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.payments.models import ManualPayment, Review
from apps.payments.validators import (
    validate_transaction_id,
    validate_payment_screenshot,
    validate_review_rating,
    validate_review_image,
)
User = get_user_model()

# ─────────────────────────────────────────────────────────────────────────────
# PAYMENT SERIALIZERS
# ─────────────────────────────────────────────────────────────────────────────

class ManualPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ManualPayment
        fields = [
            "id",
            "order",
            "transaction_id",
            "amount",
            "screenshot",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def validate_transaction_id(self, value: str) -> str:
        validate_transaction_id(value)
        value = value.strip()
        if ManualPayment.objects.filter(transaction_id=value).exists():
            raise serializers.ValidationError(
                "A payment with this transaction ID already exists."
            )
        return value

    def validate_screenshot(self, value):
        validate_payment_screenshot(value)
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class PaymentDetailSerializer(serializers.ModelSerializer):

    verified_by_email = serializers.SerializerMethodField()
    order_id = serializers.PrimaryKeyRelatedField(source="order", read_only=True)

    class Meta:
        model = ManualPayment
        fields = [
            "id",
            "order_id",
            "transaction_id",
            "amount",
            "screenshot",
            "status",
            "verified_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_verified_by_email(self, obj) -> str | None:
        if obj.verified_by:
            return obj.verified_by.email
        return None


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW SERIALIZERS
# ─────────────────────────────────────────────────────────────────────────────

class ReviewerInfoSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name"]

    def get_full_name(self, obj) -> str:
        profile = getattr(obj, "profile", None)
        if profile:
            return profile.full_name or ""
        return ""


class ReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "rating",
            "comment",
            "image",
            "is_approved",
            "created_at",
        ]
        read_only_fields = ["id", "is_approved", "created_at"]

    def validate_rating(self, value: int) -> int:
        validate_review_rating(value)
        return value

    def validate_image(self, value):
        validate_review_image(value)
        return value


class ReviewListSerializer(serializers.ModelSerializer):

    reviewer = ReviewerInfoSerializer(source="user", read_only=True)
    rating_display = serializers.SerializerMethodField()

    def get_rating_display(self, obj) -> str:
        rating = obj.rating or 0
        return "★" * rating + "☆" * (5 - rating)

    class Meta:
        model = Review
        fields = [
            "id", "reviewer", "rating", 
            "rating_display", "comment", "image", "created_at"
        ]
        read_only_fields = ["id", "rating", "comment", "image", "created_at"]

class ReviewModerationSerializer(serializers.ModelSerializer):

    reviewer = ReviewerInfoSerializer(source="user", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "reviewer",
            "rating",
            "comment",
            "image",
            "is_approved",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ReviewUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Review
        fields = ["rating", "comment", "image"]

    def validate_rating(self, value: int) -> int:
        validate_review_rating(value)
        return value

    def validate_image(self, value):
        validate_review_image(value)
        return value