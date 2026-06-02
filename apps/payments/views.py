from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from apps.core.response import api_response
from apps.core.pagination import StandardResultsSetPagination
from apps.payments import services
from apps.payments.filters import ReviewFilter
from apps.payments.serializers import ReviewListSerializer

# ─────────────────────────────────────────────────────────────────────────────
# PAYMENT VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class ManualPaymentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        data = services.submit_manual_payment(user=request.user, data=request.data)
        return api_response(True, "Payment submitted successfully.", data, 201)


class ManualPaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        data = services.get_payment_details(user=request.user, payment_id=pk)
        return api_response(True, "Payment details retrieved.", data, 200)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN PAYMENT VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class AdminPaymentApproveView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        data = services.approve_payment(admin_user=request.user, payment_id=pk)
        return api_response(True, "Payment approved and order confirmed.", data, 200)


class AdminPaymentRejectView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        data = services.reject_payment(admin_user=request.user, payment_id=pk)
        return api_response(True, "Payment rejected.", data, 200)


# ─────────────────────────────────────────────────────────────────────────────
# REVIEW VIEWS
# ─────────────────────────────────────────────────────────────────────────────

class ProductReviewListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        def apply_filter(qs):
            f = ReviewFilter(request.GET, queryset=qs, request=request)
            return f.qs

        qs = services.list_product_reviews(product_id=product_id, filterset=apply_filter)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = ReviewListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = services.create_review(user=request.user, data=request.data)
        return api_response(True, "Review submitted and pending moderation.", data, 201)


class ReviewUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, pk):
        data = services.update_review(
            user=request.user, review_id=pk, data=request.data
        )
        return api_response(True, "Review updated. Pending re-moderation.", data, 200)

    def delete(self, request, pk):
        services.delete_review(user=request.user, review_id=pk)
        return api_response(True, "Review deleted successfully.", None, 200)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN REVIEW VIEWS
# ─────────────────────────────────────────────────────────────────────────────
class AdminReviewApproveView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        data = services.approve_review(admin_user=request.user, review_id=pk)
        return api_response(True, "Review approved.", data, 200)


class AdminReviewRejectView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        data = services.reject_review(admin_user=request.user, review_id=pk)
        return api_response(True, "Review rejected.", data, 200)