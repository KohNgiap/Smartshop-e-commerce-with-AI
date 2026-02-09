from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    tags = models.CharField(max_length=300, blank=True, help_text="comma-separated tags")
    short_description = models.TextField(blank=True)

    # AI generated fields
    ai_description = models.TextField(blank=True)
    ai_review_summary = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(default=5)
    text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review({self.product.name}, {self.rating})"


class Interaction(models.Model):
    EVENT_CHOICES = [
        ("VIEW", "View"),
        ("CART", "Add to cart"),
        ("PURCHASE", "Purchase"),
        ("SEARCH", "Search"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    query_text = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}:{self.event_type}"
