from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryDetailView,
    ProductListCreateView,
    ProductDetailView,
    ProductUpdateDeleteView,
    ProductImageCreateView,
    ProductImageDeleteView,
    ProductVariantCreateView,
    ProductVariantDeleteView,
    ProductStockUpdateView,
)
from .APIRootView import ProductAPIRootView

urlpatterns = [
    path("", ProductAPIRootView.as_view(), name="product-api-root"),

    path("categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<uuid:pk>/", CategoryDetailView.as_view(), name="category-detail"),

    path("products/", ProductListCreateView.as_view(), name="product-list-create"),

    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="product-detail-by-id"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),

    path("products/<uuid:pk>/edit/", ProductUpdateDeleteView.as_view(), name="product-update-delete"),
    path("products/<uuid:pk>/stock/", ProductStockUpdateView.as_view(), name="product-stock-update"),
    path("products/<uuid:pk>/images/", ProductImageCreateView.as_view(), name="product-image-create"),
    path("images/<uuid:pk>/", ProductImageDeleteView.as_view(), name="product-image-delete"),
    path("products/<uuid:pk>/variants/", ProductVariantCreateView.as_view(), name="product-variant-create"),
    path("variants/<uuid:pk>/", ProductVariantDeleteView.as_view(), name="product-variant-delete"),
]