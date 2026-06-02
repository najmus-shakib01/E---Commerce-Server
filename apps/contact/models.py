import uuid
from django.db import models
from .constants import InquirySubject

class Inquiry(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=150)
    email = models.EmailField(db_index=True)
    subject = models.CharField(
        max_length=30,
        choices=InquirySubject.CHOICES,
        default=InquirySubject.GENERAL_INQUIRY,
        db_index=True,
    )
    message = models.TextField()

    is_read = models.BooleanField(
        default=False,
        help_text="অ্যাডমিন মেসেজটি পড়েছেন কিনা।",
    )
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inquiries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"],      name="idx_inquiry_email"),
            models.Index(fields=["subject"],    name="idx_inquiry_subject"),
            models.Index(fields=["is_read"],    name="idx_inquiry_is_read"),
            models.Index(fields=["created_at"], name="idx_inquiry_created"),
        ]

    def __str__(self):
        return f"[{self.get_subject_display()}] {self.name} <{self.email}>"

    @property
    def subject_bangla(self) -> str:
        return InquirySubject.BANGLA_LABELS.get(self.subject, self.subject)

    @property
    def subject_badge_color(self) -> str:
        return InquirySubject.BADGE_COLORS.get(self.subject, "#6b7280")