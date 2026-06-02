from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Inquiry

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "subject_badge",
        "short_message",
        "read_status",
        "created_at",
    ]
    list_filter  = ["subject", "is_read", "created_at"]
    search_fields = ["name", "email", "message"]
    readonly_fields = ["id", "created_at", "updated_at", "read_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("প্রেরকের তথ্য", {
            "fields": ("id", "name", "email"),
        }),
        ("ইনকোয়ারি", {
            "fields": ("subject", "message"),
        }),
        ("Admin ট্র্যাকিং", {
            "fields": ("is_read", "read_at"),
        }),
        ("টাইমস্ট্যাম্প", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request)

    @admin.display(description="বিষয়")
    def subject_badge(self, obj):
        color = obj.subject_badge_color
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:11px;font-weight:700;">{}</span>',
            color,
            obj.subject_bangla,
        )

    @admin.display(description="মেসেজ (সংক্ষেপ)")
    def short_message(self, obj):
        return obj.message[:60] + "..." if len(obj.message) > 60 else obj.message

    @admin.display(description="পড়া হয়েছে?")
    def read_status(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color:#16a34a;font-weight:600;">✓ পড়া হয়েছে</span>'
            )
        return format_html(
            '<span style="color:#dc2626;font-weight:600;">● অপঠিত</span>'
        )

    def save_model(self, request, obj, form, change):
        """is_read True হলে read_at সেট করো।"""
        if obj.is_read and not obj.read_at:
            obj.read_at = timezone.now()
        super().save_model(request, obj, form, change)