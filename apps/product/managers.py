from django.db import models
from django.db.models import Case, When, F, DecimalField, Avg, Count, Q

class CategoryQuerySet(models.QuerySet):
    def top_level(self):
        return self.filter(parent__isnull=True)

    def with_children(self):
        return self.prefetch_related("children")


class CategoryManager(models.Manager):
    def get_queryset(self) -> CategoryQuerySet:
        return CategoryQuerySet(self.model, using=self._db)

    def top_level(self):
        return self.get_queryset().top_level()

    def with_children(self):
        return self.get_queryset().with_children()


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def in_stock(self):
        return self.filter(stock_quantity__gt=0)

    def out_of_stock(self):
        return self.filter(stock_quantity=0)

    def by_category(self, category_id):
        return self.filter(category_id=category_id)

    def with_relations(self):
        return self.select_related("category").prefetch_related("images", "variants")

    def annotate_final_price(self):
        """
        computed_price annotation — future use বা direct queryset filter এর জন্য।
        """
        if "computed_price" in self.query.annotations:
            return self  
        return self.annotate(
            computed_price=Case(
                When(discount_price__isnull=False, then=F("discount_price")),
                default=F("regular_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )

    def with_review_stats(self):
        """
        Annotates each product with average_rating and total_reviews.
        Only counts approved reviews. Avoids N+1 queries.
        """
        approved = Q(reviews__is_approved=True)
        return self.annotate(
            average_rating=Avg("reviews__rating", filter=approved),
            total_reviews=Count("reviews", filter=approved),
        )


class ProductManager(models.Manager):
    def get_queryset(self) -> ProductQuerySet:
        return ProductQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def in_stock(self):
        return self.get_queryset().active().in_stock()

    def with_relations(self):
        return self.get_queryset().with_relations()

    def with_review_stats(self):
        return self.get_queryset().with_review_stats()