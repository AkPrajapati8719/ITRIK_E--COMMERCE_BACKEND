from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated

from .models import Category, Product, Review
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ReviewSerializer,
    CreateReviewSerializer,
)


# =========================
# CATEGORY
# =========================

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly]


# =========================
# PRODUCT
# =========================

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "category__name"]
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = (
            Product.objects
            .select_related("category")
            .prefetch_related(
                "reviews",
                "images",     # 📸 gallery
                "features",   # ✔ feature points
            )
        )

        # ⭐ FEATURED PRODUCTS (HOMEPAGE)
        featured = self.request.query_params.get("featured")
        if featured == "true":
            queryset = queryset.filter(
                is_featured=True,
                stock__gt=0,
                main_image__isnull=False
            )

        # CATEGORY FILTER
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        # PRICE FILTER
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")

        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # STOCK FILTER
        in_stock = self.request.query_params.get("in_stock")
        if in_stock == "true":
            queryset = queryset.filter(stock__gt=0)

        return queryset

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    # =========================
    # ADD REVIEW
    # =========================

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def add_review(self, request, slug=None):
        product = self.get_object()

        serializer = CreateReviewSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)

        return Response(
            {
                "success": True,
                "message": "Review added successfully"
            },
            status=status.HTTP_201_CREATED
        )


# =========================
# REVIEW
# =========================

class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Review.objects.select_related("user", "product")
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()

        product_id = self.request.query_params.get("product_id")
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset