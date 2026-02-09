from rest_framework import serializers
from .models import Product, Review, Interaction


class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "price",
            "image",  # returns full URL or null
            "tags",
            "short_description",
            "ai_description",
            "ai_review_summary",
        ]

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "product", "user", "rating", "text", "created_at"]


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ["id", "user", "product", "event_type", "query_text", "created_at"]
