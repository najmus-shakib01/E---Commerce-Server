from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant
from .validators import (
    validate_image_file,
    validate_discount_price,
    validate_stock_quantity,
)
from .constants import VariantType

# ─────────────────────────────────────────────
# CATEGORY SERIALIZERS
# ─────────────────────────────────────────────

class CategoryChildSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]

class CategorySerializer(serializers.ModelSerializer):

    children = CategoryChildSerializer(many=True, read_only=True)
    parent_name = serializers.CharField(source="parent.name", read_only=True, default=None)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "parent_name",
            "children",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Category name cannot be blank.")
        return value

class CategoryWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["name", "parent"]

    def validate_name(self, value: str) -> str:
        return value.strip()

    def validate(self, attrs: dict) -> dict:
        parent = attrs.get("parent")
        name = attrs.get("name", "")

        qs = Category.objects.filter(name__iexact=name, parent=parent)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                {"name": "A category with this name already exists under the same parent."}
            )
        return attrs


# ─────────────────────────────────────────────
# IMAGE SERIALIZER
# ─────────────────────────────────────────────
class ProductImageSerializer(serializers.ModelSerializer):

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "image_url", "is_primary", "created_at"]
        read_only_fields = ["id", "image_url", "created_at"]
        extra_kwargs = {
            "image": {"write_only": True, "required": True},
        }

    def get_image_url(self, obj: ProductImage) -> str | None:
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None

    def validate_image(self, image):
        validate_image_file(image)
        return image


# ─────────────────────────────────────────────
# VARIANT SERIALIZER
# ─────────────────────────────────────────────
class ProductVariantSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "type", "type_display", "value"]
        read_only_fields = ["id", "type_display"]

    def validate_value(self, value: str) -> str:
        return value.strip()

    def validate_type(self, value: str) -> str:
        valid = [v for v, _ in VariantType.choices]
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid variant type. Choose from: {', '.join(valid)}."
            )
        return value


# ─────────────────────────────────────────────
# PRODUCT LIST SERIALIZER
# ─────────────────────────────────────────────

class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    final_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    is_in_stock = serializers.BooleanField(
        read_only=True
    )
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "category_name",
            "regular_price", "discount_price", "final_price",
            "discount_percentage", "primary_image", "is_in_stock",
            "stock_quantity", "created_at",
        ]

    def get_primary_image(self, obj: Product) -> str | None:
        request = self.context.get("request")
        primary = next((img for img in obj.images.all() if img.is_primary), None)
        if not primary:
            primary = next(iter(obj.images.all()), None)
        if primary and primary.image:
            if request:
                return request.build_absolute_uri(primary.image.url)
            return primary.image.url
        return None
    
# ─────────────────────────────────────────────
# PRODUCT DETAIL SERIALIZER
# ─────────────────────────────────────────────

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategoryChildSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    final_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    is_in_stock = serializers.BooleanField(
        read_only=True
    )
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    related_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "name", "slug", "description", "category",
            "regular_price", "discount_price", "final_price",
            "discount_percentage", "stock_quantity", "is_in_stock",
            "is_active", "images", "variants", "related_products",
            "created_at", "updated_at",
        ]

    def get_related_products(self, obj: Product) -> list:
        from .constants import RELATED_PRODUCTS_LIMIT
        related_qs = (
            Product.objects.active()
            .filter(category=obj.category)
            .exclude(pk=obj.pk)
            .with_relations()
            .order_by("-created_at")[:RELATED_PRODUCTS_LIMIT]
        )
        return ProductListSerializer(
            related_qs, many=True, context=self.context
        ).data

# ─────────────────────────────────────────────
# PRODUCT WRITE SERIALIZER
# ─────────────────────────────────────────────

class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "description",
            "regular_price",
            "discount_price",
            "stock_quantity",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_regular_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Regular price must be greater than zero.")
        return value

    def validate_discount_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Discount price cannot be negative.")
        return value

    def validate_stock_quantity(self, value):
        validate_stock_quantity(value)
        return value

    def validate(self, attrs: dict) -> dict:
        regular_price = attrs.get("regular_price", getattr(self.instance, "regular_price", None))
        discount_price = attrs.get("discount_price", getattr(self.instance, "discount_price", None))
        try:
            validate_discount_price(discount_price, regular_price)
        except Exception as e:
            raise serializers.ValidationError({"discount_price": str(e)})
        return attrs


# ─────────────────────────────────────────────
# INVENTORY UPDATE SERIALIZER
# ─────────────────────────────────────────────

class StockUpdateSerializer(serializers.Serializer):
    """Serializer for updating product stock quantity."""

    stock_quantity = serializers.IntegerField(min_value=0)

    def validate_stock_quantity(self, value: int) -> int:
        validate_stock_quantity(value)
        return value