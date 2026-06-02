from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.urls import reverse, NoReverseMatch
from apps.core.response import api_response
from .models import Inquiry

class ContactAPIRootView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        sample = Inquiry.objects.order_by("-created_at").first()
        sample_id = str(sample.id) if sample else "00000000-0000-0000-0000-000000000000"

        def build(name, **kwargs):
            try:
                return request.build_absolute_uri(
                    reverse(f"contact:{name}", kwargs=kwargs)
                )
            except NoReverseMatch:
                return None

        endpoints = {
            "module": "Contact & Inquiry",
            "version": "v1",
            "base_url": request.build_absolute_uri("/api/v1/contact/"),

            "public": {
                "submit_inquiry": {
                    "url": build("contact-submit"),
                    "method": "POST",
                    "auth_required": False,
                    "body": {
                        "name":    "string (min 2 chars)",
                        "email":   "valid email address",
                        "subject": "GENERAL_INQUIRY | ORDER_ISSUE | PRODUCT_FEEDBACK | TECHNICAL_SUPPORT",
                        "message": "string (min 10, max 3000 chars)",
                    },
                    "note": "ইউজার সাবমিট করলে Admin ও ইউজার দুজনেই ইমেইল পাবেন।",
                },
            },

            "admin": {
                "note": "Admin endpoints — IsAdminUser permission required.",
                "list_inquiries": {
                    "url": build("admin-list"),
                    "method": "GET",
                    "filters": "?subject=ORDER_ISSUE&is_read=false",
                    "note": "summary (total/unread/read) পেজিনেশনের সাথে দেয়।",
                },
                "inquiry_detail": {
                    "url": build("admin-detail", id=sample_id),
                    "method": "GET",
                },
                "mark_read": {
                    "url": build("admin-mark-read", id=sample_id),
                    "method": "PATCH",
                    "body": {"is_read": True},
                },
                "reply_to_user": {
                    "url": build("admin-reply", id=sample_id),
                    "method": "POST",
                    "body": {"reply_message": "আপনার সমস্যার সমাধান হলো..."},
                    "note": "ইউজারের ইমেইলে রিপ্লাই পাঠাবে এবং inquiry auto-read মার্ক হবে।",
                },
            },

            "subject_choices": {
                "GENERAL_INQUIRY":  "সাধারণ জিজ্ঞাসা",
                "ORDER_ISSUE":      "অর্ডার সমস্যা",
                "PRODUCT_FEEDBACK": "পণ্যের মতামত",
                "TECHNICAL_SUPPORT":"প্রযুক্তিগত সহায়তা",
            },
        }

        return api_response(True, "Contact Module API Root", endpoints, 200)