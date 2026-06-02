from django.urls import path
from apps.payments.views import (
    ManualPaymentCreateView,
    ManualPaymentDetailView,
    AdminPaymentApproveView,
    AdminPaymentRejectView,
    ProductReviewListView,
    ReviewCreateView,
    ReviewUpdateDeleteView,
    AdminReviewApproveView,
    AdminReviewRejectView,
)
from apps.payments.APIRootView import PaymentAPIRootView

urlpatterns = [
    # API Root
    path("", PaymentAPIRootView.as_view(), name="payment-api-root"),

    # Payment APIs
    path("manual/", ManualPaymentCreateView.as_view(), name="manual-payment-create"),
    path("manual/<int:pk>/", ManualPaymentDetailView.as_view(), name="manual-payment-detail"),

    # Admin Payment APIs
    path("admin/manual/<int:pk>/approve/", AdminPaymentApproveView.as_view(), name="admin-payment-approve"),
    path("admin/manual/<int:pk>/reject/", AdminPaymentRejectView.as_view(), name="admin-payment-reject"),

    # Review APIs
    path("reviews/product/<uuid:product_id>/", ProductReviewListView.as_view(), name="product-review-list"),
    path("reviews/", ReviewCreateView.as_view(), name="review-create"),
    path("reviews/<int:pk>/", ReviewUpdateDeleteView.as_view(), name="review-update-delete"),

    # Admin Review APIs
    path("admin/reviews/<int:pk>/approve/", AdminReviewApproveView.as_view(), name="admin-review-approve"),
    path("admin/reviews/<int:pk>/reject/", AdminReviewRejectView.as_view(), name="admin-review-reject"),
]