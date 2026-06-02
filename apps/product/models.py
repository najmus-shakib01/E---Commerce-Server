import uuid
from django.db import models
from django.utils.text import slugify
from .managers import CategoryManager, ProductManager
from .constants import VariantType
from .validators import (
    validate_image_file,
    validate_discount_price,
    validate_stock_quantity,
)

class Category(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CategoryManager()

    class Meta:
        db_table = "product_categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="idx_category_slug"),
            models.Index(fields=["parent"], name="idx_category_parent"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "parent"],
                name="unique_category_name_per_parent",
            )
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    @property
    def is_subcategory(self) -> bool:
        return self.parent_id is not None

    @property
    def full_path(self) -> str:
        """Returns full category path e.g. 'Electronics > Phones > Samsung'."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Product(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )
    name = models.CharField(max_length=512, db_index=True)
    slug = models.SlugField(max_length=600, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    regular_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"], name="idx_product_slug"),
            models.Index(fields=["is_active", "created_at"], name="idx_product_active_created"),
            models.Index(fields=["category", "is_active"], name="idx_product_category_active"),
            models.Index(fields=["regular_price"], name="idx_product_price"),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def clean(self) -> None:
        validate_discount_price(self.discount_price, self.regular_price)
        validate_stock_quantity(self.stock_quantity)

    def __str__(self) -> str:
        return self.name

    @property
    def final_price(self):
        """Returns discount_price if set and valid, otherwise regular_price."""
        if self.discount_price and self.discount_price < self.regular_price:
            return self.discount_price
        return self.regular_price

    @property
    def is_in_stock(self) -> bool:
        """Returns True if stock_quantity > 0."""
        return self.stock_quantity > 0

    @property
    def discount_percentage(self):
        """Returns discount percentage if discount_price is set."""
        if self.discount_price and self.regular_price > 0:
            discount = ((self.regular_price - self.discount_price) / self.regular_price) * 100
            return round(discount, 2)
        return None


class ProductImage(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        db_index=True,
    )
    image = models.ImageField(
        upload_to="products/",
        validators=[validate_image_file],
    )
    is_primary = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_images"
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        ordering = ["-is_primary", "created_at"]
        indexes = [
            models.Index(fields=["product", "is_primary"], name="idx_product_primary_image"),
        ]

    def save(self, *args, **kwargs) -> None:
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        label = "Primary" if self.is_primary else "Secondary"
        return f"{self.product.name} [{label}]"


class ProductVariant(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        db_index=True,
    )
    type = models.CharField(
        max_length=10,
        choices=VariantType.choices,
        db_index=True,
    )
    value = models.CharField(max_length=100)

    class Meta:
        db_table = "product_variants"
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        ordering = ["type", "value"]
        indexes = [
            models.Index(fields=["product", "type"], name="idx_variant_product_type"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "type", "value"],
                name="unique_product_variant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.type}: {self.value}"