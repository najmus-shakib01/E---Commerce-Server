import logging
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Inquiry
from .email_service import (
    send_admin_notification,
    send_user_acknowledgement,
    send_admin_reply,
)
logger = logging.getLogger(__name__)


def submit_inquiry(validated_data: dict) -> Inquiry:
    inquiry = Inquiry.objects.create(**validated_data)

    logger.info(
        f"[Contact] New inquiry created | id={inquiry.id} | "
        f"email={inquiry.email} | subject={inquiry.subject}"
    )

    admin_sent = send_admin_notification(inquiry)
    if not admin_sent:
        logger.warning(f"[Contact] Admin notification failed | inquiry={inquiry.id}")

    user_sent = send_user_acknowledgement(inquiry)
    if not user_sent:
        logger.warning(f"[Contact] User ack email failed | inquiry={inquiry.id}")

    return inquiry


def list_inquiries(filters: dict = None):
    qs = Inquiry.objects.all()

    if filters:
        if "subject" in filters and filters["subject"]:
            qs = qs.filter(subject=filters["subject"])
        if "is_read" in filters and filters["is_read"] is not None:
            qs = qs.filter(is_read=filters["is_read"])

    return qs


def get_inquiry(inquiry_id: str) -> Inquiry:
    return get_object_or_404(Inquiry, id=inquiry_id)


def mark_inquiry_read(inquiry: Inquiry, is_read: bool) -> Inquiry:
    inquiry.is_read = is_read
    inquiry.read_at = timezone.now() if is_read else None
    inquiry.save(update_fields=["is_read", "read_at", "updated_at"])

    logger.info(
        f"[Contact] Inquiry {'read' if is_read else 'unread'} | id={inquiry.id}"
    )
    return inquiry


def reply_to_inquiry(inquiry: Inquiry, reply_message: str) -> Inquiry:
    sent = send_admin_reply(inquiry, reply_message)

    if sent:
        if not inquiry.is_read:
            inquiry.is_read = True
            inquiry.read_at = timezone.now()
            inquiry.save(update_fields=["is_read", "read_at", "updated_at"])

        logger.info(
            f"[Contact] Admin reply sent | inquiry={inquiry.id} | to={inquiry.email}"
        )
    else:
        logger.error(
            f"[Contact] Admin reply FAILED | inquiry={inquiry.id} | to={inquiry.email}"
        )
        from rest_framework.exceptions import ValidationError
        raise ValidationError(
            "ইমেইল পাঠাতে সমস্যা হয়েছে। আবার চেষ্টা করুন।"
        )

    return inquiry