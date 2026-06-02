import logging
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAdminUser
from apps.core.response import api_response
from apps.core.pagination import StandardResultsSetPagination
from .serializers import (
    InquiryCreateSerializer,
    InquiryListSerializer,
    InquiryDetailSerializer,
    InquiryMarkReadSerializer,
    InquiryReplySerializer,
)
from .services import (
    submit_inquiry,
    list_inquiries,
    get_inquiry,
    mark_inquiry_read,
    reply_to_inquiry,
)
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC — Contact Form Submission
# ══════════════════════════════════════════════════════════════════════════════

class ContactFormView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = InquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        inquiry = submit_inquiry(serializer.validated_data)

        return api_response(
            True,
            "আপনার মেসেজ সফলভাবে পাঠানো হয়েছে। "
            "আমরা শীঘ্রই আপনার ইমেইলে সাড়া দেব।",
            {"inquiry_id": str(inquiry.id)},
            201,
        )


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Inquiry Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class AdminInquiryListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Query param filters
        subject  = request.query_params.get("subject")
        is_read_param = request.query_params.get("is_read")

        is_read = None
        if is_read_param is not None:
            is_read = is_read_param.lower() == "true"

        filters = {"subject": subject, "is_read": is_read}
        queryset = list_inquiries(filters)

        # Statistics for dashboard
        total   = queryset.count()
        unread  = queryset.filter(is_read=False).count()

        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = InquiryListSerializer(page, many=True)

        response_data = paginator.get_paginated_response(serializer.data).data
        response_data["summary"] = {
            "total":  total,
            "unread": unread,
            "read":   total - unread,
        }

        return api_response(True, "Inquiry list retrieved.", response_data, 200)


class AdminInquiryDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, id):
        inquiry = get_inquiry(str(id))
        serializer = InquiryDetailSerializer(inquiry)
        return api_response(True, "Inquiry detail retrieved.", serializer.data, 200)


class AdminInquiryMarkReadView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, id):
        inquiry = get_inquiry(str(id))
        serializer = InquiryMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        inquiry = mark_inquiry_read(
            inquiry,
            is_read=serializer.validated_data["is_read"],
        )
        detail = InquiryDetailSerializer(inquiry)
        msg = "পড়া হয়েছে মার্ক করা হয়েছে।" if inquiry.is_read else "অপঠিত মার্ক করা হয়েছে।"
        return api_response(True, msg, detail.data, 200)


class AdminInquiryReplyView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, id):
        inquiry = get_inquiry(str(id))
        serializer = InquiryReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reply_to_inquiry(
            inquiry=inquiry,
            reply_message=serializer.validated_data["reply_message"],
        )

        return api_response(
            True,
            f"রিপ্লাই সফলভাবে {inquiry.email}-এ পাঠানো হয়েছে।",
            {
                "inquiry_id": str(inquiry.id),
                "replied_to": inquiry.email,
            },
            200,
        )