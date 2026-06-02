import logging
from typing import Optional
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, NotFound
from .models import Category, Product, ProductImage, ProductVariant
from .validators import validate_discount_price, validate_stock_quantity
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════
# CATEGORY SERVICES
# ═══════════════════════════════════════════════

class CategoryService:
    """All business logic for Category management."""

    @staticmethod
    def list_categories(parent_id: Optional[str] = None):
        """parent_id এখন UUID string।"""
        if parent_id:
            return Category.objects.filter(
                parent_id=parent_id
            ).prefetch_related("children").order_by("name")

        return (
            Category.objects
            .filter(parent__isnull=True)
            .prefetch_related("children")
            .order_by("name")
        )

    @staticmethod
    @transaction.atomic
    def create_category(name: str, parent_id: Optional[int] = None) -> Category:
        parent = None
        if parent_id:
            try:
                parent = Category.objects.get(pk=parent_id)
            except Category.DoesNotExist:
                raise NotFound(f"Parent category with id={parent_id} not found.")
        if Category.objects.filter(name__iexact=name, parent=parent).exists():
            raise ValidationError(
                {"name": "A category with this name already exists under the same parent."}
            )

        category = Category.objects.create(name=name, parent=parent)
        logger.info(f"Category created: id={category.id}, name={category.name}")
        return category

    @staticmethod
    @transaction.atomic
    def update_category(
        category_id: int,
        name: Optional[str] = None,
        parent_id: Optional[int] = None,
        partial: bool = False,
    ) -> Category:

        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            raise NotFound(f"Category with id={category_id} not found.")

        if name is not None:
            name = name.strip()
            qs = Category.objects.filter(
                name__iexact=name, parent_id=parent_id if parent_id else category.parent_id
            ).exclude(pk=category_id)
            if qs.exists():
                raise ValidationError(
                    {"name": "A category with this name already exists under the same parent."}
                )
            category.name = name

        if parent_id is not None:
            if parent_id == category_id:
                raise ValidationError({"parent": "A category cannot be its own parent."})
            try:
                parent = Category.objects.get(pk=parent_id)
                category.parent = parent
            except Category.DoesNotExist:
                raise NotFound(f"Parent category with id={parent_id} not found.")
        elif not partial and parent_id is None:
            category.parent = None

        if name is not None:
            category.slug = "" 

        category.save()
        logger.info(f"Category updated: id={category.id}")
        return category

    @staticmethod
    @transaction.atomic
    def delete_category(category_id: int) -> None:
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            raise NotFound(f"Category with id={category_id} not found.")

        if category.children.exists():
            raise ValidationError(
                {"detail": "Cannot delete a category that has subcategories."}
            )
        if category.products.filter(is_active=True).exists():
            raise ValidationError(
                {"detail": "Cannot delete a category that has active products."}
            )

        category.delete()
        logger.info(f"Category deleted: id={category_id}")


# ═══════════════════════════════════════════════
# PRODUCT SERVICES
# ═══════════════════════════════════════════════

class ProductService:

    @staticmethod
    def list_products(filters: dict = None):
  
        return (
            Product.objects
            .active()
            .select_related("category")
            .prefetch_related("images", "variants")
            .order_by("-created_at")
        )

    @staticmethod
    def retrieve_product(slug: str) -> Product:

        try:
            return (
                Product.objects
                .active()
                .select_related("category")
                .prefetch_related("images", "variants")
                .get(slug=slug)
            )
        except Product.DoesNotExist:
            raise NotFound(f"Product with slug='{slug}' not found.")

    @staticmethod
    @transaction.atomic
    def create_product(validated_data: dict) -> Product:
     
        regular_price = validated_data.get("regular_price")
        discount_price = validated_data.get("discount_price")

        try:
            validate_discount_price(discount_price, regular_price)
        except Exception as e:
            raise ValidationError({"discount_price": str(e)})

        product = Product.objects.create(**validated_data)
        logger.info(f"Product created: id={product.id}, name={product.name}")
        return product

    @staticmethod
    @transaction.atomic
    def update_product(product_id: int, validated_data: dict, partial: bool = False) -> Product:

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id={product_id} not found.")

        regular_price = validated_data.get("regular_price", product.regular_price)
        discount_price = validated_data.get("discount_price", product.discount_price)

        try:
            validate_discount_price(discount_price, regular_price)
        except Exception as e:
            raise ValidationError({"discount_price": str(e)})

        for attr, value in validated_data.items():
            setattr(product, attr, value)

        if "name" in validated_data:
            product.slug = ""

        product.save()
        logger.info(f"Product updated: id={product.id}")

        return (
            Product.objects
            .select_related("category")
            .prefetch_related("images", "variants")
            .get(pk=product.pk)
        )
    
    @staticmethod
    def retrieve_product_by_id(product_id) -> Product:
     
        try:
            return (
                Product.objects
                .active()
                .select_related("category")
                .prefetch_related("images", "variants")
                .get(pk=product_id)
            )
        except Product.DoesNotExist:
            raise NotFound(f"Product with id='{product_id}' not found.")

    @staticmethod
    @transaction.atomic
    def delete_product(product_id: int) -> None:
  
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id={product_id} not found.")

        product.is_active = False
        product.save(update_fields=["is_active", "updated_at"])
        logger.info(f"Product deactivated: id={product_id}")


# ═══════════════════════════════════════════════
# IMAGE SERVICES
# ═══════════════════════════════════════════════

class ProductImageService:

    @staticmethod
    @transaction.atomic
    def add_product_image(product_id: int, image, is_primary: bool = False) -> ProductImage:

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id={product_id} not found.")

        if is_primary:
            ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)

        product_image = ProductImage.objects.create(
            product=product,
            image=image,
            is_primary=is_primary,
        )
        logger.info(f"Image added to product id={product_id}, image id={product_image.id}")
        return product_image

    @staticmethod
    @transaction.atomic
    def update_product_image(image_id: int, is_primary: bool) -> ProductImage:

        try:
            product_image = ProductImage.objects.select_related("product").get(pk=image_id)
        except ProductImage.DoesNotExist:
            raise NotFound(f"ProductImage with id={image_id} not found.")

        if is_primary:
            ProductImage.objects.filter(
                product=product_image.product, is_primary=True
            ).exclude(pk=image_id).update(is_primary=False)

        product_image.is_primary = is_primary
        product_image.save(update_fields=["is_primary"])
        return product_image

    @staticmethod
    @transaction.atomic
    def delete_product_image(image_id: int) -> None:
        try:
            product_image = ProductImage.objects.select_related("product").get(pk=image_id)
        except ProductImage.DoesNotExist:
            raise NotFound(f"ProductImage with id={image_id} not found.")

        total_images = ProductImage.objects.filter(product=product_image.product).count()
        if total_images <= 1:
            raise ValidationError(
                {"detail": "Cannot delete the only image of a product."}
            )

        product_image.image.delete(save=False) 
        product_image.delete()
        logger.info(f"Image deleted: id={image_id}")


# ═══════════════════════════════════════════════
# VARIANT SERVICES
# ═══════════════════════════════════════════════

class ProductVariantService:

    @staticmethod
    @transaction.atomic
    def add_variant(product_id: int, variant_type: str, value: str) -> ProductVariant:
 
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id={product_id} not found.")

        if ProductVariant.objects.filter(
            product=product,
            type=variant_type,
            value__iexact=value.strip(),
        ).exists():
            raise ValidationError(
                {"detail": f"Variant '{variant_type}: {value}' already exists for this product."}
            )

        variant = ProductVariant.objects.create(
            product=product,
            type=variant_type,
            value=value.strip(),
        )
        logger.info(f"Variant added: product id={product_id}, variant id={variant.id}")
        return variant

    @staticmethod
    @transaction.atomic
    def remove_variant(variant_id: int) -> None:
        try:
            variant = ProductVariant.objects.get(pk=variant_id)
        except ProductVariant.DoesNotExist:
            raise NotFound(f"Variant with id={variant_id} not found.")

        variant.delete()
        logger.info(f"Variant deleted: id={variant_id}")


# ═══════════════════════════════════════════════
# INVENTORY SERVICES
# ═══════════════════════════════════════════════

class InventoryService:
    @staticmethod
    @transaction.atomic
    def update_stock(product_id: int, quantity: int) -> Product:
        try:
            validate_stock_quantity(quantity)
        except Exception as e:
            raise ValidationError({"stock_quantity": str(e)})

        try:
            product = Product.objects.select_for_update().get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id={product_id} not found.")

        product.stock_quantity = quantity
        product.save(update_fields=["stock_quantity", "updated_at"])
        logger.info(f"Stock updated: product id={product_id}, new quantity={quantity}")
        return product

    @staticmethod
    def validate_stock(product_id: int, requested_qty: int) -> bool:
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            raise NotFound(f"Product with id={product_id} not found.")

        if product.stock_quantity < requested_qty:
            raise ValidationError(
                {
                    "detail": (
                        f"Only {product.stock_quantity} unit(s) available. "
                        f"Requested: {requested_qty}."
                    )
                }
            )
        return True