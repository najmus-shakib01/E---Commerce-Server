from django.db import models

class ManualPaymentQuerySet(models.QuerySet):

    def pending(self):
        return self.filter(status="PENDING")

    def approved(self):
        return self.filter(status="APPROVED")

    def rejected(self):
        return self.filter(status="REJECTED")

    def with_relations(self):
        return self.select_related("order", "order__user", "verified_by")

class ManualPaymentManager(models.Manager):

    def get_queryset(self):
        return ManualPaymentQuerySet(self.model, using=self._db)

    def pending(self):
        return self.get_queryset().pending()

    def approved(self):
        return self.get_queryset().approved()

    def with_relations(self):
        return self.get_queryset().with_relations()

class ReviewQuerySet(models.QuerySet):

    def approved(self):
        return self.filter(is_approved=True)

    def pending(self):
        return self.filter(is_approved=False)

    def for_product(self, product_id):
        return self.filter(product_id=product_id)

    def with_relations(self):
        return self.select_related("user", "user__profile", "product")

class ReviewManager(models.Manager):

    def get_queryset(self):
        return ReviewQuerySet(self.model, using=self._db)

    def approved(self):
        return self.get_queryset().approved()

    def for_product(self, product_id):
        return self.get_queryset().for_product(product_id)

    def with_relations(self):
        return self.get_queryset().with_relations()