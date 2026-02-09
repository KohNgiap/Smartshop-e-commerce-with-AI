from django.urls import path
from . import views

urlpatterns = [
    # UI
    path("", views.home, name="home"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),

    # APIs
    path("api/products/", views.api_products, name="api_products"),
    path("api/search/", views.api_search, name="api_search"),
    path("api/recommendations/<str:username>/", views.api_recommendations, name="api_recommendations"),
    path("api/products/<int:product_id>/generate-description/", views.api_generate_description, name="api_generate_description"),
    path("api/products/<int:product_id>/summarize-reviews/", views.api_summarize_reviews, name="api_summarize_reviews"),
    path("api/chat/", views.api_chat, name="api_chat"),
]
