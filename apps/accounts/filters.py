import django_filters
from .models import User
from .constants import UserRole

class UserFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=UserRole.choices)
    is_active = django_filters.BooleanFilter()
    is_banned = django_filters.BooleanFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = User
        fields = ["role", "is_active", "is_banned"]