import django_filters
from .models import Order
from .constants import OrderStatus, PaymentMethod

class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        choices=OrderStatus.CHOICES,
        label="Order Status",
    )
    payment_method = django_filters.ChoiceFilter(
        choices=PaymentMethod.CHOICES,
        label="Payment Method",
    )
    created_after = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        label="Created After (YYYY-MM-DD)",
    )
    created_before = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        label="Created Before (YYYY-MM-DD)",
    )
    ordering = django_filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
        ),
        field_labels={
            "created_at": "Date (newest first by default)",
        },
    )

    class Meta:
        model = Order
        fields = ["status", "payment_method", "created_after", "created_before"]