from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.urls import reverse
from apps.core.response import api_response
from .models import Product, Category

class ProductAPIRootView(APIView):

    permission_classes = [AllowAny]

    def _url(self, request, name: str, **kwargs) -> str:
        try:
            return request.build_absolute_uri(reverse(name, kwargs=kwargs))
        except Exception:
            return ""

    def get(self, request):
        sample_product = (
            Product.objects
            .active()
            .only("slug")
            .first()
        )
        sample_slug = sample_product.slug if sample_product else "sample-product-slug"
        sample_product_id = sample_product.id if sample_product else 1

        sample_category = Category.objects.only("id").first()
        sample_category_id = sample_category.id if sample_category else 1

        endpoints = {
            "module": "Product & Inventory Module",
            "base_url": request.build_absolute_uri(reverse("product-api-root")),
            "categories": {
                "list_create": {
                    "url": self._url(request, "category-list-create"),
                    "methods": ["GET", "POST"],
                    "description": "GET: List all categories | POST: Create category (Admin)",
                },
                "detail": {
                    "url": self._url(request, "category-detail", pk=sample_category_id),
                    "methods": ["GET", "PUT", "PATCH", "DELETE"],
                    "description": "GET/PUT/PATCH/DELETE a specific category by id",
                },
                "filter_subcategories": {
                    "url": self._url(request, "category-list-create") + f"?parent_id={sample_category_id}",
                    "methods": ["GET"],
                    "description": "Filter subcategories by parent_id query param",
                },
            },
            "products": {
                "list_create": {
                    "url": self._url(request, "product-list-create"),
                    "methods": ["GET", "POST"],
                    "description": "GET: List products (public, filterable) | POST: Create (Admin)",
                },
                "detail": {
                    "url": self._url(request, "product-detail", slug=sample_slug),
                    "methods": ["GET"],
                    "description": "GET product detail by slug (public)",
                },
                "update_delete": {
                    "url": self._url(request, "product-update-delete", pk=sample_product_id),
                    "methods": ["PUT", "PATCH", "DELETE"],
                    "description": "PUT/PATCH/DELETE a product by id (Admin only)",
                },
                "stock_update": {
                    "url": self._url(request, "product-stock-update", pk=sample_product_id),
                    "methods": ["PATCH"],
                    "description": "Update product stock quantity (Admin only)",
                },
            },
            "images": {
                "upload": {
                    "url": self._url(request, "product-image-create", pk=sample_product_id),
                    "methods": ["POST"],
                    "description": "Upload image for a product (Admin only, multipart/form-data)",
                },
                "delete": {
                    "url": self._url(request, "product-image-delete", pk=1),
                    "methods": ["DELETE"],
                    "description": "Delete a product image by image id (Admin only)",
                },
            },
            "variants": {
                "add": {
                    "url": self._url(request, "product-variant-create", pk=sample_product_id),
                    "methods": ["POST"],
                    "description": "Add variant to a product (Admin only)",
                },
                "remove": {
                    "url": self._url(request, "product-variant-delete", pk=1),
                    "methods": ["DELETE"],
                    "description": "Remove a product variant by variant id (Admin only)",
                },
            },
            "query_params": {
                "search": "?search=<keyword>   → search by name, description, category",
                "category": "?category=<id>    → filter by category id",
                "min_price": "?min_price=<num> → minimum price filter",
                "max_price": "?max_price=<num> → maximum price filter",
                "in_stock": "?in_stock=true    → show only in-stock products",
                "sort": "?sort=low_to_high | high_to_low | newest | oldest | popular",
                "page": "?page=<n>             → pagination page number",
                "page_size": "?page_size=<n>   → results per page (max 500)",
            },
        }

        return api_response(True, "Product Module API Root", endpoints, 200)