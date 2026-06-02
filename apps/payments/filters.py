import django_filters
from apps.payments.models import Review, ManualPayment
from apps.payments.constants import PaymentStatus

class ReviewFilter(django_filters.FilterSet):

    rating = django_filters.NumberFilter(field_name="rating", lookup_expr="exact")
    min_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")
    max_rating = django_filters.NumberFilter(field_name="rating", lookup_expr="lte")
    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "newest"),
            ("rating", "rating"),
        ),
        field_labels={
            "newest": "Newest First",
            "-newest": "Oldest First",
            "rating": "Lowest Rating",
            "-rating": "Highest Rating",
        },
    )

    class Meta:
        model = Review
        fields = ["rating", "min_rating", "max_rating"]


class ManualPaymentFilter(django_filters.FilterSet):
    """Filter payments by status for admin."""

    status = django_filters.ChoiceFilter(choices=PaymentStatus.CHOICES)

    class Meta:
        model = ManualPayment
        fields = ["status"]