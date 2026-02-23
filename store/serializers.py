from rest_framework import serializers
from .models import (
    Category,
    Product,
    Review,
    ProductImage,
    ProductFeature,
)


# =========================
# CATEGORY
# =========================

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


# =========================
# PRODUCT IMAGE (GALLERY)
# =========================

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["image"]

    def get_image(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url)


# =========================
# PRODUCT FEATURE POINTS
# =========================

class ProductFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFeature
        fields = ["text"]


# =========================
# REVIEW
# =========================

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user_name", "rating", "comment", "created_at"]
        read_only_fields = ["id", "created_at"]


# =========================
# PRODUCT LIST (INDEX / SHOP)
# =========================

class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    image = serializers.SerializerMethodField()

    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "discount_price",
            "category",
            "image",
            "avg_rating",
            "review_count",
            "is_featured",
            "stock",
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.main_image.url)

    def get_avg_rating(self, obj):
        return obj.get_average_rating()

    def get_review_count(self, obj):
        return obj.reviews.count()


# =========================
# PRODUCT DETAIL (FULL DATA)
# =========================

class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    images = ProductImageSerializer(many=True, read_only=True)
    features = ProductFeatureSerializer(many=True, read_only=True)

    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    main_image = serializers.SerializerMethodField()
    video_file = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "price",
            "discount_price",
            "stock",
            "main_image",
            "images",       # 📸 gallery (1–6)
            "features",     # ✔ feature points (1–15)
            "video_file",
            "is_featured",
            "category",
            "reviews",
            "avg_rating",
            "review_count",
            "created_at",
            "updated_at",
        ]

    def get_main_image(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.main_image.url)

    def get_video_file(self, obj):
        if not obj.video_file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.video_file.url)

    def get_avg_rating(self, obj):
        return obj.get_average_rating()

    def get_review_count(self, obj):
        return obj.reviews.count()


# =========================
# CREATE REVIEW
# =========================

class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["product", "rating", "comment"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)