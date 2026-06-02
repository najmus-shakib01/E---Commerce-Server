import django_filters
from django.db.models import QuerySet, Case, When, F, DecimalField, Q
from .models import Product
from .constants import SortOption

class ProductFilter(django_filters.FilterSet):

    # ✅ Exact এর বদলে কাস্টম মেথড ব্যবহার করা হলো
    category = django_filters.UUIDFilter(
        method="filter_category_hierarchy",
        label="Category UUID",
    )
    subcategory = django_filters.UUIDFilter(
        field_name="category_id",
        lookup_expr="exact",
        label="Subcategory UUID",
    )
    min_price = django_filters.NumberFilter(
        method="filter_min_price",
        label="Minimum Price",
    )
    max_price = django_filters.NumberFilter(
        method="filter_max_price",
        label="Maximum Price",
    )
    in_stock = django_filters.BooleanFilter(
        method="filter_in_stock",
        label="In Stock Only",
    )
    search = django_filters.CharFilter(
        method="filter_search",
        label="Search",
    )
    sort = django_filters.CharFilter(
        method="filter_sort",
        label="Sort",
    )

    class Meta:
        model = Product
        fields = [
            "category",
            "subcategory",
            "min_price",
            "max_price",
            "in_stock",
            "search",
            "sort",
        ]

    # ──────────────────────────────────────────────────────
    # HELPER: safe price annotation (duplicate-safe)
    # ──────────────────────────────────────────────────────
    @staticmethod
    def _annotate_price(queryset: QuerySet) -> QuerySet:

        if "computed_price" in queryset.query.annotations:
            return queryset
        return queryset.annotate(
            computed_price=Case(
                When(discount_price__isnull=False, then=F("discount_price")),
                default=F("regular_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )

    # ──────────────────────────────────────────────────────
    # FILTER METHODS
    # ──────────────────────────────────────────────────────

    # ✅ নতুন মেথড: এটি প্যারেন্ট এবং সাব-ক্যাটাগরি উভয়ের প্রোডাক্ট খুঁজবে
    def filter_category_hierarchy(self, queryset: QuerySet, name: str, value) -> QuerySet:
        return queryset.filter(
            Q(category_id=value) | Q(category__parent_id=value)
        ).distinct()

    def filter_min_price(self, queryset: QuerySet, name: str, value) -> QuerySet:
        """final_price >= value"""
        return self._annotate_price(queryset).filter(computed_price__gte=value)

    def filter_max_price(self, queryset: QuerySet, name: str, value) -> QuerySet:
        """final_price <= value"""
        return self._annotate_price(queryset).filter(computed_price__lte=value)

    def filter_in_stock(self, queryset: QuerySet, name: str, value: bool) -> QuerySet:
        """in_stock=true → stock > 0 | in_stock=false → stock == 0"""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)

    def filter_search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        """name, description বা category name এ keyword search।"""
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(category__name__icontains=value)
        ).distinct()

    def filter_sort(self, queryset: QuerySet, name: str, value: str) -> QuerySet:

        sort_map = {
            SortOption.LOW_TO_HIGH: "regular_price",
            SortOption.HIGH_TO_LOW: "-regular_price",
            SortOption.NEWEST:      "-created_at",
            SortOption.OLDEST:      "created_at",
            SortOption.POPULAR:     "-stock_quantity",
        }
        order_field = sort_map.get(value)
        return queryset.order_by(order_field) if order_field else queryset
