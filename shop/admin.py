from django.contrib import admin
from .models import Product, Review, Interaction

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    search_fields = ("name", "category", "tags")

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "rating", "created_at")
    search_fields = ("product__name", "text")

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "product", "created_at")
    search_fields = ("user__username", "event_type", "query_text")
