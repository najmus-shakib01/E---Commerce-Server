import logging
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from apps.core.response import api_response
from apps.core.pagination import StandardResultsSetPagination

from .models import Category
from .serializers import (
    CategorySerializer,
    CategoryWriteSerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductVariantSerializer,
    StockUpdateSerializer,
)
from .services import (
    CategoryService,
    ProductService,
    ProductImageService,
    ProductVariantService,
    InventoryService,
)
from .filters import ProductFilter
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════
# CATEGORY VIEWS
# ═══════════════════════════════════════════════

class CategoryListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request: Request) -> Response:
        parent_id = request.query_params.get("parent_id")
        
        categories = CategoryService.list_categories(parent_id=parent_id or None)
        
        serializer = CategorySerializer(categories, many=True, context={"request": request})
        return api_response(True, "Categories retrieved successfully.", serializer.data, 200)

    def post(self, request: Request) -> Response:
        serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        category = CategoryService.create_category(
            name=serializer.validated_data["name"],
            parent_id=serializer.validated_data.get("parent", {}).id
            if serializer.validated_data.get("parent")
            else None,
        )
        out = CategorySerializer(category, context={"request": request})
        return api_response(True, "Category created successfully.", out.data, 201)


class CategoryDetailView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def _get_category(self, pk) -> Category:  
        try:
            return Category.objects.prefetch_related("children").get(pk=pk)
        except Category.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Category with id={pk} not found.")

    def get(self, request: Request, pk: int) -> Response:
        category = self._get_category(pk)
        serializer = CategorySerializer(category, context={"request": request})
        return api_response(True, "Category retrieved successfully.", serializer.data, 200)

    def put(self, request: Request, pk: int) -> Response:
        serializer = CategoryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parent = serializer.validated_data.get("parent")
        category = CategoryService.update_category(
            category_id=pk,
            name=serializer.validated_data.get("name"),
            parent_id=parent.id if parent else None,
            partial=False,
        )
        out = CategorySerializer(category, context={"request": request})
        return api_response(True, "Category updated successfully.", out.data, 200)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = CategoryWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        parent = serializer.validated_data.get("parent")
        category = CategoryService.update_category(
            category_id=pk,
            name=serializer.validated_data.get("name"),
            parent_id=parent.id if parent else None,
            partial=True,
        )
        out = CategorySerializer(category, context={"request": request})
        return api_response(True, "Category updated successfully.", out.data, 200)

    def delete(self, request: Request, pk: int) -> Response:
        CategoryService.delete_category(pk)
        return api_response(True, "Category deleted successfully.", None, 200)


# ═══════════════════════════════════════════════
# PRODUCT VIEWS
# ═══════════════════════════════════════════════

class ProductListCreateView(APIView):

    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request: Request) -> Response:
        queryset = ProductService.list_products()

        product_filter = ProductFilter(request.query_params, queryset=queryset, request=request)
        queryset = product_filter.qs

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(queryset, many=True, context={"request": request})
        return api_response(True, "Products retrieved successfully.", serializer.data, 200)

    def post(self, request: Request) -> Response:
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = ProductService.create_product(serializer.validated_data)
        out = ProductDetailSerializer(product, context={"request": request})
        return api_response(True, "Product created successfully.", out.data, 201)


class ProductDetailView(APIView):

    permission_classes = [AllowAny]

    def get(self, request: Request, slug: str = None, pk=None) -> Response:
        if pk is not None:
            product = ProductService.retrieve_product_by_id(pk)
        else:
            product = ProductService.retrieve_product(slug)
        serializer = ProductDetailSerializer(product, context={"request": request})
        return api_response(True, "Product retrieved successfully.", serializer.data, 200)

class ProductUpdateDeleteView(APIView):

    permission_classes = [IsAdminUser]

    def put(self, request: Request, pk: int) -> Response:
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = ProductService.update_product(pk, serializer.validated_data, partial=False)
        out = ProductDetailSerializer(product, context={"request": request})
        return api_response(True, "Product updated successfully.", out.data, 200)

    def patch(self, request: Request, pk: int) -> Response:
        serializer = ProductSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        product = ProductService.update_product(pk, serializer.validated_data, partial=True)
        out = ProductDetailSerializer(product, context={"request": request})
        return api_response(True, "Product updated successfully.", out.data, 200)

    def delete(self, request: Request, pk: int) -> Response:
        ProductService.delete_product(pk)
        return api_response(True, "Product deleted (deactivated) successfully.", None, 200)


# ═══════════════════════════════════════════════
# IMAGE VIEWS
# ═══════════════════════════════════════════════

class ProductImageCreateView(APIView):

    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: Request, pk: int) -> Response:
        serializer = ProductImageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        image_obj = ProductImageService.add_product_image(
            product_id=pk,
            image=serializer.validated_data["image"],
            is_primary=serializer.validated_data.get("is_primary", False),
        )
        out = ProductImageSerializer(image_obj, context={"request": request})
        return api_response(True, "Image uploaded successfully.", out.data, 201)


class ProductImageDeleteView(APIView):

    permission_classes = [IsAdminUser]

    def delete(self, request: Request, pk: int) -> Response:
        ProductImageService.delete_product_image(pk)
        return api_response(True, "Image deleted successfully.", None, 200)


# ═══════════════════════════════════════════════
# VARIANT VIEWS
# ═══════════════════════════════════════════════

class ProductVariantCreateView(APIView):

    permission_classes = [IsAdminUser]

    def post(self, request: Request, pk: int) -> Response:
        serializer = ProductVariantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant = ProductVariantService.add_variant(
            product_id=pk,
            variant_type=serializer.validated_data["type"],
            value=serializer.validated_data["value"],
        )
        out = ProductVariantSerializer(variant)
        return api_response(True, "Variant added successfully.", out.data, 201)


class ProductVariantDeleteView(APIView):

    permission_classes = [IsAdminUser]

    def delete(self, request: Request, pk: int) -> Response:
        ProductVariantService.remove_variant(pk)
        return api_response(True, "Variant removed successfully.", None, 200)


# ═══════════════════════════════════════════════
# INVENTORY VIEW
# ═══════════════════════════════════════════════

class ProductStockUpdateView(APIView):

    permission_classes = [IsAdminUser]

    def patch(self, request: Request, pk: int) -> Response:
        serializer = StockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = InventoryService.update_stock(
            product_id=pk,
            quantity=serializer.validated_data["stock_quantity"],
        )
        return api_response(
            True,
            "Stock updated successfully.",
            {
                "id": product.id,
                "name": product.name,
                "stock_quantity": product.stock_quantity,
                "is_in_stock": product.is_in_stock,
            },
            200,
        )