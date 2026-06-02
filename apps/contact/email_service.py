import logging
from typing import Optional
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
logger = logging.getLogger(__name__)

def _get_admin_emails() -> list[str]:
    admin_emails = getattr(settings, "CONTACT_ADMIN_EMAILS", None)
    if admin_emails:
        return admin_emails if isinstance(admin_emails, list) else [admin_emails]
    return [settings.EMAIL_HOST_USER]


def _send_email(
    subject: str,
    template_name: str,
    context: dict,
    to_emails: list[str],
    reply_to: Optional[list[str]] = None,
) -> bool:
    try:
        html_body  = render_to_string(template_name, context)
        plain_body = strip_tags(html_body)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,  
            to=to_emails,
            reply_to=reply_to,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        logger.info(
            f"[ContactEmail] Sent '{template_name}' → {to_emails}"
        )
        return True

    except Exception as exc:
        logger.error(
            f"[ContactEmail] FAILED '{template_name}' → {to_emails} | {exc}",
            exc_info=True,
        )
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 1. Admin Notification
# ──────────────────────────────────────────────────────────────────────────────

def send_admin_notification(inquiry) -> bool:
    subject = (
        f"📩 [{inquiry.name}] — {inquiry.subject_bangla}" 
    )
    context = {"inquiry": inquiry}
    admin_emails = _get_admin_emails()

    return _send_email(
        subject=subject,
        template_name="contact/inquiry_admin_notification.html",
        context=context,
        to_emails=admin_emails,
        reply_to=[inquiry.email], 
    )


# ──────────────────────────────────────────────────────────────────────────────
# 2. User Acknowledgement
# ──────────────────────────────────────────────────────────────────────────────

def send_user_acknowledgement(inquiry) -> bool:
    subject = "✅ আপনার মেসেজ পেয়েছি — Shaistaganj E-shop"
    context = {"inquiry": inquiry}

    return _send_email(
        subject=subject,
        template_name="contact/inquiry_user_ack.html",
        context=context,
        to_emails=[inquiry.email],
    )


# ──────────────────────────────────────────────────────────────────────────────
# 3. Admin Reply to User
# ──────────────────────────────────────────────────────────────────────────────

def send_admin_reply(inquiry, reply_message: str) -> bool:
    subject = f"💬 আপনার ইনকোয়ারির উত্তর — {inquiry.get_subject_display()} | Shaistaganj E-shop"
    context = {
        "inquiry": inquiry,
        "reply_message": reply_message,
    }
    admin_emails = _get_admin_emails()

    return _send_email(
        subject=subject,
        template_name="contact/inquiry_admin_reply.html",
        context=context,
        to_emails=[inquiry.email],
        reply_to=admin_emails,  
    )