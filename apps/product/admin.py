from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductVariant

# ─────────────────────────────────────────────
# CATEGORY ADMIN
# ─────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug", "parent", "created_at"]
    list_filter = ["parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]
    list_select_related = ["parent"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {"fields": ("name", "slug", "parent")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


# ─────────────────────────────────────────────
# PRODUCT IMAGE INLINE
# ─────────────────────────────────────────────

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "image_preview", "is_primary", "created_at"]
    readonly_fields = ["image_preview", "created_at"]

    def image_preview(self, obj: ProductImage):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:4px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Preview"


# ─────────────────────────────────────────────
# PRODUCT VARIANT INLINE
# ─────────────────────────────────────────────

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ["type", "value"]


# ─────────────────────────────────────────────
# PRODUCT ADMIN
# ─────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "category",
        "regular_price",
        "discount_price",
        "stock_quantity",
        "is_active",
        "is_in_stock_display",
        "created_at",
    ]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["name", "slug", "description", "category__name"]
    ordering = ["-created_at"]
    readonly_fields = ["slug", "created_at", "updated_at", "primary_image_preview"]
    list_select_related = ["category"]
    list_per_page = 25

    inlines = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        ("Basic Info", {
            "fields": ("category", "name", "slug", "description", "is_active")
        }),
        ("Pricing", {
            "fields": ("regular_price", "discount_price")
        }),
        ("Inventory", {
            "fields": ("stock_quantity",)
        }),
        ("Preview", {
            "fields": ("primary_image_preview",),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def is_in_stock_display(self, obj: Product) -> str:
        if obj.is_in_stock:
            return format_html('<span style="color:green;">✔ In Stock</span>')
        return format_html('<span style="color:red;">✘ Out of Stock</span>')

    is_in_stock_display.short_description = "Stock Status"

    def primary_image_preview(self, obj: Product):
        primary = obj.images.filter(is_primary=True).first()
        if primary and primary.image:
            return format_html(
                '<img src="{}" style="height:100px; border-radius:4px;" />',
                primary.image.url,
            )
        return "No primary image"

    primary_image_preview.short_description = "Primary Image"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .prefetch_related("images", "variants")
        )


# ─────────────────────────────────────────────
# PRODUCT IMAGE ADMIN
# ─────────────────────────────────────────────

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "image_preview", "is_primary", "created_at"]
    list_filter = ["is_primary"]
    search_fields = ["product__name"]
    readonly_fields = ["image_preview", "created_at"]
    list_select_related = ["product"]

    def image_preview(self, obj: ProductImage):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:50px; border-radius:4px;" />',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Preview"


# ─────────────────────────────────────────────
# PRODUCT VARIANT ADMIN
# ─────────────────────────────────────────────

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "type", "value"]
    list_filter = ["type"]
    search_fields = ["product__name", "value"]
    list_select_related = ["product"]