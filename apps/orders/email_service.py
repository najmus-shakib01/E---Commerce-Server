import logging
import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .constants import OrderStatus, PaymentMethod
logger = logging.getLogger(__name__)
from .constants import DELIVERY_CHARGE_INSIDE, DeliveryZone
from decimal import Decimal

# ── Internal Helpers ──────────────────────────────────────────────────────────

def _get_support_email() -> str:
    return getattr(settings, "EMAIL_HOST_USER", "support@shaistaganj-eshop.com")

def _build_item_context(order) -> list[dict]:
    items = []
    for item in order.items.select_related("product"):
        items.append({
            "product_name": item.product.name,
            "quantity": item.quantity,
            "price": item.price,
            "line_total": item.line_total,
        })
    return items

def _get_payment_method_display(payment_method: str) -> str:
    mapping = {
        PaymentMethod.COD: "Cash on Delivery (COD)",
        PaymentMethod.MANUAL_MFS: "Manual Mobile Banking / Bank",
    }
    return mapping.get(payment_method, payment_method)


def _get_delivery_zone_display(order) -> str:
    try:
        if hasattr(order, "delivery_zone"):
            zone = order.delivery_zone
            if zone == DeliveryZone.INSIDE:
                return "শায়েস্তাগঞ্জ (ভেতরে)"
            return "শায়েস্তাগঞ্জের বাইরে"

        if order.delivery_charge == Decimal(str(DELIVERY_CHARGE_INSIDE)):
            return "শায়েস্তাগঞ্জ (ভেতরে)"
        return "শায়েস্তাগঞ্জের বাইরে"
    except Exception:
        return "—"


def _get_user_full_name(order) -> str:
    """User profile থেকে full_name নেয়, না পেলে email fallback।"""
    try:
        profile = order.user.profile 
        if profile and profile.full_name:
            return profile.full_name
    except Exception:
        pass
    return order.user.email


def _send_email_async(subject: str, to_email: str, html_content: str) -> None:
    def _send():
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body="",  
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
            logger.info(f"[OrderEmail] Sent '{subject}' → {to_email}")
        except Exception as exc:
            logger.error(
                f"[OrderEmail] Failed to send '{subject}' → {to_email}: {exc}",
                exc_info=True,
            )

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


# ── Public API ────────────────────────────────────────────────────────────────

def send_order_placed_email(order) -> None:
    try:
        full_name = _get_user_full_name(order)
        items = _build_item_context(order)
        payment_method = order.payment_method

        context = {
            "full_name": full_name,
            "order_number": order.order_number,
            "items": items,
            "subtotal": order.subtotal,
            "delivery_charge": order.delivery_charge,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "payment_method_display": _get_payment_method_display(payment_method),
            "delivery_zone_display": _get_delivery_zone_display(order),
            "is_cod": payment_method == PaymentMethod.COD,
            "is_manual_payment": payment_method == PaymentMethod.MANUAL_MFS,
            "support_email": _get_support_email(),
        }

        html = render_to_string("orders/order_placed.html", context)
        _send_email_async(
            subject=f"✅ অর্ডার কনফার্মেশন — {order.order_number}",
            to_email=order.user.email,
            html_content=html,
        )
    except Exception as exc:
        logger.error(f"[OrderEmail] send_order_placed_email error: {exc}", exc_info=True)


def send_order_confirmed_email(order) -> None:
    try:
        context = {
            "full_name": _get_user_full_name(order),
            "order_number": order.order_number,
            "items": _build_item_context(order),
            "subtotal": order.subtotal,
            "delivery_charge": order.delivery_charge,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "support_email": _get_support_email(),
        }
        html = render_to_string("orders/order_confirmed.html", context)
        _send_email_async(
            subject=f"🎉 অর্ডার কনফার্মড — {order.order_number}",
            to_email=order.user.email,
            html_content=html,
        )
    except Exception as exc:
        logger.error(f"[OrderEmail] send_order_confirmed_email error: {exc}", exc_info=True)


def send_order_shipped_email(order) -> None:
    try:
        context = {
            "full_name": _get_user_full_name(order),
            "order_number": order.order_number,
            "items": _build_item_context(order),
            "subtotal": order.subtotal,
            "delivery_charge": order.delivery_charge,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "courier_name": order.courier_name or "",
            "tracking_id": order.tracking_id or "",
            "support_email": _get_support_email(),
        }
        html = render_to_string("orders/order_shipped.html", context)
        _send_email_async(
            subject=f"🚚 আপনার পণ্য পাঠানো হয়েছে — {order.order_number}",
            to_email=order.user.email,
            html_content=html,
        )
    except Exception as exc:
        logger.error(f"[OrderEmail] send_order_shipped_email error: {exc}", exc_info=True)


def send_order_delivered_email(order) -> None:
    try:
        context = {
            "full_name": _get_user_full_name(order),
            "order_number": order.order_number,
            "items": _build_item_context(order),
            "subtotal": order.subtotal,
            "delivery_charge": order.delivery_charge,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "support_email": _get_support_email(),
        }
        html = render_to_string("orders/order_delivered.html", context)
        _send_email_async(
            subject=f"📦 পণ্য ডেলিভারি সম্পন্ন — {order.order_number}",
            to_email=order.user.email,
            html_content=html,
        )
    except Exception as exc:
        logger.error(f"[OrderEmail] send_order_delivered_email error: {exc}", exc_info=True)


def send_order_cancelled_email(order, cancellation_note: str = "") -> None:
    try:
        context = {
            "full_name": _get_user_full_name(order),
            "order_number": order.order_number,
            "items": _build_item_context(order),
            "subtotal": order.subtotal,
            "delivery_charge": order.delivery_charge,
            "total_amount": order.total_amount,
            "cancellation_note": cancellation_note,
            "is_manual_payment": order.payment_method == PaymentMethod.MANUAL_MFS,
            "support_email": _get_support_email(),
        }
        html = render_to_string("orders/order_cancelled.html", context)
        _send_email_async(
            subject=f"❌ অর্ডার বাতিল — {order.order_number}",
            to_email=order.user.email,
            html_content=html,
        )
    except Exception as exc:
        logger.error(f"[OrderEmail] send_order_cancelled_email error: {exc}", exc_info=True)


# ── Auto-Dispatch by Status ───────────────────────────────────────────────────

_STATUS_EMAIL_MAP = {
    OrderStatus.CONFIRMED: send_order_confirmed_email,
    OrderStatus.SHIPPED: send_order_shipped_email,
    OrderStatus.DELIVERED: send_order_delivered_email,
    OrderStatus.CANCELLED: send_order_cancelled_email,
}


def send_order_status_email(order, new_status: str, cancellation_note: str = "") -> None:
    if new_status == OrderStatus.CANCELLED:
        send_order_cancelled_email(order, cancellation_note=cancellation_note)
        return

    fn = _STATUS_EMAIL_MAP.get(new_status)
    if fn:
        fn(order)
    else:
        logger.debug(f"[OrderEmail] No email mapped for status: {new_status}")