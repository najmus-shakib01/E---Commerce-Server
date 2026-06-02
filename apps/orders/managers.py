from django.db import models
from .constants import OrderStatus

class CartItemQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def with_product(self):
        return self.select_related("product")


class CartItemManager(models.Manager):
    def get_queryset(self):
        return CartItemQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user).with_product()


# ─── Wishlist Manager ─────────────────────────────────────────────────────────
class WishlistQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def with_product(self):
        return self.select_related("product", "product__category").prefetch_related("product__images")


class WishlistManager(models.Manager):
    def get_queryset(self):
        return WishlistQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user).with_product()


# ─── Order Manager ────────────────────────────────────────────────────────────
class OrderQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def pending(self):
        return self.filter(status=OrderStatus.PENDING)

    def active(self):
        return self.exclude(status=OrderStatus.CANCELLED)

    def with_items(self):
        return self.prefetch_related(
            models.Prefetch(
                "items",
                queryset=__import__(
                    "apps.orders.models", fromlist=["OrderItem"]
                ).OrderItem.objects.select_related("product"),
            )
        )

    def with_full_detail(self):
        return self.select_related("user").prefetch_related(
            "items__product",
            "status_logs__changed_by",
        )


class OrderManager(models.Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def with_full_detail(self):
        return self.get_queryset().with_full_detail()