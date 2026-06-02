from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.urls import reverse
from apps.core.response import api_response
from apps.payments.models import ManualPayment, Review

class PaymentAPIRootView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        sample_payment = ManualPayment.objects.only("id").first()
        sample_review = Review.objects.only("id").first()
        sample_payment_id = sample_payment.id if sample_payment else 1
        sample_review_id = sample_review.id if sample_review else 1
        sample_product_id = (
            Review.objects.values_list("product_id", flat=True).first() or 1
        )

        def url(name, **kwargs):
            try:
                return request.build_absolute_uri(reverse(name, kwargs=kwargs))
            except Exception:
                return None

        endpoints = {
            "module": "Payments & Reviews",
            "version": "v1",
            "base_url": request.build_absolute_uri(reverse("payment-api-root")),
            "payment_endpoints": {
                "submit_payment": {
                    "url": url("manual-payment-create"),
                    "method": "POST",
                    "auth": "Required",
                    "description": "Submit manual MFS/bank payment with screenshot",
                },
                "payment_detail": {
                    "url": url("manual-payment-detail", pk=sample_payment_id),
                    "method": "GET",
                    "auth": "Required",
                    "description": "Get payment details by ID",
                },
                "admin_approve_payment": {
                    "url": url("admin-payment-approve", pk=sample_payment_id),
                    "method": "PATCH",
                    "auth": "Admin Only",
                    "description": "Approve payment and confirm order",
                },
                "admin_reject_payment": {
                    "url": url("admin-payment-reject", pk=sample_payment_id),
                    "method": "PATCH",
                    "auth": "Admin Only",
                    "description": "Reject payment, order stays pending",
                },
            },
            "review_endpoints": {
                "product_reviews": {
                    "url": url("product-review-list", product_id=sample_product_id),
                    "method": "GET",
                    "auth": "Public",
                    "description": "List approved reviews for a product",
                    "filters": ["rating", "min_rating", "max_rating", "ordering"],
                },
                "create_review": {
                    "url": url("review-create"),
                    "method": "POST",
                    "auth": "Required",
                    "description": "Submit review (only for purchased & delivered products)",
                },
                "update_review": {
                    "url": url("review-update-delete", pk=sample_review_id),
                    "method": "PATCH",
                    "auth": "Required (Owner)",
                    "description": "Update own review",
                },
                "delete_review": {
                    "url": url("review-update-delete", pk=sample_review_id),
                    "method": "DELETE",
                    "auth": "Required (Owner)",
                    "description": "Delete own review",
                },
                "admin_approve_review": {
                    "url": url("admin-review-approve", pk=sample_review_id),
                    "method": "PATCH",
                    "auth": "Admin Only",
                    "description": "Approve review for public visibility",
                },
                "admin_reject_review": {
                    "url": url("admin-review-reject", pk=sample_review_id),
                    "method": "PATCH",
                    "auth": "Admin Only",
                    "description": "Reject and hide review",
                },
            },
        }

        return api_response(True, "Payments & Reviews API Root", endpoints, 200)