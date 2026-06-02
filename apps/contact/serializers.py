from rest_framework import serializers
from .models import Inquiry

# ─── Public: Contact Form Submission ─────────────────────────────────────────

class InquiryCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Inquiry
        fields = ["name", "email", "subject", "message"]

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("নাম কমপক্ষে ২ অক্ষরের হতে হবে।")
        return value

    def validate_message(self, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("মেসেজ কমপক্ষে ১০ অক্ষরের হতে হবে।")
        if len(value) > 3000:
            raise serializers.ValidationError("মেসেজ সর্বোচ্চ ৩০০০ অক্ষরের হতে পারবে।")
        return value


# ─── Admin: List View ─────────────────────────────────────────────────────────

class InquiryListSerializer(serializers.ModelSerializer):
    subject_display = serializers.CharField(
        source="get_subject_display", read_only=True
    )
    subject_bangla = serializers.CharField(read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "name",
            "email",
            "subject",
            "subject_display",
            "subject_bangla",
            "is_read",
            "created_at",
        ]


# ─── Admin: Detail View ───────────────────────────────────────────────────────

class InquiryDetailSerializer(serializers.ModelSerializer):
    subject_display = serializers.CharField(
        source="get_subject_display", read_only=True
    )
    subject_bangla  = serializers.CharField(read_only=True)
    subject_badge_color = serializers.CharField(read_only=True)

    class Meta:
        model = Inquiry
        fields = [
            "id",
            "name",
            "email",
            "subject",
            "subject_display",
            "subject_bangla",
            "subject_badge_color",
            "message",
            "is_read",
            "read_at",
            "created_at",
            "updated_at",
        ]


# ─── Admin: Mark as Read ─────────────────────────────────────────────────────

class InquiryMarkReadSerializer(serializers.Serializer):
    is_read = serializers.BooleanField()


# ─── Admin: Reply ─────────────────────────────────────────────────────────────

class InquiryReplySerializer(serializers.Serializer):
    reply_message = serializers.CharField(
        min_length=10,
        max_length=5000,
        help_text="Admin এর রিপ্লাই মেসেজ।",
    )

    def validate_reply_message(self, value: str) -> str:
        return value.strip()