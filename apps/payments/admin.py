from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from apps.payments.models import ManualPayment, Review
from apps.payments.constants import PaymentStatus

# ─────────────────────────────────────────────────────────────────────────────
# MANUAL PAYMENT ADMIN
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(ManualPayment)
class ManualPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order_link",
        "transaction_id",
        "amount_display",
        "status_badge",
        "screenshot_preview",
        "verified_by",
        "created_at",
    ]
    list_filter = ["status", "created_at", "updated_at"]
    search_fields = ["transaction_id", "order__id", "order__order_number"] 
    
    readonly_fields = [
        "id", "order", "transaction_id", "amount", 
        "screenshot_preview_large", "verified_by", "created_at", "updated_at"
    ]
    
    fieldsets = (
        (_("Transaction Details"), {
            "fields": ("id", "order", "transaction_id", "amount", "status")
        }),
        (_("Verification Info"), {
            "fields": ("screenshot_preview_large", "verified_by")
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    actions = ["mark_as_approved", "mark_as_rejected"]

    def order_link(self, obj):
        return f"Order #{obj.order.id}"
    order_link.short_description = "Order"

    def amount_display(self, obj):
        return f"{obj.amount} BDT"
    amount_display.short_description = "Amount"

    def status_badge(self, obj):
        colors = {
            PaymentStatus.PENDING: "#f39c12", 
            PaymentStatus.APPROVED: "#27ae60", 
            PaymentStatus.REJECTED: "#e74c3c", 
        }
        color = colors.get(obj.status, "#7f8c8d")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    def screenshot_preview(self, obj):
        if obj.screenshot:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:4px; border:1px solid #ddd;" /></a>',
                obj.screenshot.url, obj.screenshot.url
            )
        return "No image"
    screenshot_preview.short_description = "Screenshot"

    def screenshot_preview_large(self, obj):
        if obj.screenshot:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="300" style="border-radius:8px;" /></a>',
                obj.screenshot.url, obj.screenshot.url
            )
        return "No image"
    screenshot_preview_large.short_description = "Proof Image"

    # --- Actions ---

    @admin.action(description="Mark selected payments as Approved")
    def mark_as_approved(self, request, queryset):
        updated = queryset.update(status=PaymentStatus.APPROVED, verified_by=request.user)
        self.message_user(request, f"{updated} payments have been approved.")

    @admin.action(description="Mark selected payments as Rejected")
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status=PaymentStatus.REJECTED, verified_by=request.user)
        self.message_user(request, f"{updated} payments have been rejected.")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "verified_by")


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW ADMIN
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "product",
        "user_email",
        "rating_stars",
        "truncated_comment",
        "is_approved",
        "review_image_preview",
        "created_at",
    ]
    list_filter = ["is_approved", "rating", "created_at"]
    list_editable = ["is_approved"] 
    search_fields = ["user__email", "product__name", "comment"]
    
    readonly_fields = [
        "id", "product", "user", "rating_stars", "review_image_large", "created_at", "updated_at"
    ]

    fieldsets = (
        (_("Review Info"), {
            "fields": ("id", "product", "user", "rating", "rating_stars", "comment")
        }),
        (_("Media"), {
            "fields": ("review_image_large",)
        }),
        (_("Moderation"), {
            "fields": ("is_approved",)
        }),
        (_("Timestamps"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    actions = ["approve_reviews", "reject_reviews"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Reviewer"

    def rating_stars(self, obj):
        # Handle cases where rating is None (like the 'Add' page)
        if obj.rating is None:
            return "No rating yet"
        
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        color = "#f1c40f" if obj.rating >= 4 else "#95a5a6"
        return format_html('<span style="color: {}; font-size: 14px;">{}</span>', color, stars)
    rating_stars.short_description = "Rating"

    def truncated_comment(self, obj):
        if not obj.comment:
            return "—"
        if len(obj.comment) > 50:
            return f"{obj.comment[:50]}..."
        return obj.comment
    truncated_comment.short_description = "Comment"

    def review_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="40" style="object-fit:cover; border-radius:4px;" />',
                obj.image.url
            )
        return "—"
    review_image_preview.short_description = "Img"

    def review_image_large(self, obj):
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="250" style="border-radius:8px;" /></a>',
                obj.image.url, obj.image.url
            )
        return "No image attached"
    review_image_large.short_description = "Uploaded Image"

    # --- Actions ---

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Selected reviews are now public.")

    @admin.action(description="Reject/Hide selected reviews")
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "Selected reviews have been hidden.")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "product")