from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import Product, Interaction, Review
import random

class Command(BaseCommand):
    help = "Seed sample products, users, interactions, and reviews (no image URLs required)"

    def handle(self, *args, **kwargs):
        # --- 1) Create users ---
        users = []
        for username in ["alice", "bob", "charlie"]:
            u, created = User.objects.get_or_create(username=username)
            if created:
                u.set_password("password123")
                u.save()
            users.append(u)

        # --- 2) Create products (NO images; upload later in admin) ---
        # Note: name must be unique-ish; we use get_or_create so re-running won't duplicate
        sample_products = [
            # name, category, price, tags, short_description
            ("Wireless Earbuds", "Electronics", 49.90, "audio,wireless,gym", "Compact wireless earbuds for music and calls."),
            ("Gaming Mouse", "Electronics", 29.90, "gaming,pc,accessory", "Ergonomic mouse with precise tracking."),
            ("Running Shoes", "Fashion", 89.00, "sports,fitness,comfort", "Lightweight shoes designed for daily runs."),
            ("Coffee Maker", "Home", 79.00, "kitchen,coffee,morning", "Brew fresh coffee quickly and easily."),
            ("Backpack", "Fashion", 39.00, "travel,school,bag", "Durable backpack for work, school, or travel."),
            ("Smart Watch", "Electronics", 119.00, "health,fitness,wearable", "Track fitness, sleep, and notifications."),
            ("Blender", "Home", 55.00, "kitchen,smoothie,healthy", "Blend smoothies, shakes, and sauces fast."),
            ("Sunglasses", "Fashion", 25.00, "summer,style,uv", "UV protection with a modern style."),
            ("Laptop Stand", "Office", 19.90, "desk,ergonomic,work", "Improve posture with an adjustable stand."),
            ("Yoga Mat", "Sports", 18.00, "fitness,yoga,home-workout", "Non-slip mat for yoga and stretching."),
        ]

        products = []
        for name, cat, price, tags, desc in sample_products:
            p, _ = Product.objects.get_or_create(
                name=name,
                defaults={
                    "category": cat,
                    "price": price,
                    "tags": tags,
                    "short_description": desc,
                    # No image set here. Upload later in admin.
                    # "image": None  # not needed
                }
            )
            products.append(p)

        # --- 3) Create interactions (simulate behavior) ---
        event_types = ["VIEW", "CART", "PURCHASE"]
        for u in users:
            # simulate browse/cart/purchase
            for _ in range(30):
                p = random.choice(products)
                e = random.choices(event_types, weights=[0.7, 0.2, 0.1])[0]
                Interaction.objects.create(user=u, product=p, event_type=e)

            # simulate searches
            for q in ["wireless audio", "cheap fitness gear", "kitchen appliances", "office ergonomic"]:
                Interaction.objects.create(user=u, event_type="SEARCH", query_text=q)

        # --- 4) Create reviews ---
        sample_reviews = [
            (5, "Great quality and works perfectly."),
            (4, "Good value for money. I like it."),
            (3, "It’s okay, but could be better."),
            (2, "Not very durable. Disappointed."),
        ]

        for p in products:
            # Ensure each product has a few reviews
            for _ in range(4):
                rating, text = random.choice(sample_reviews)
                Review.objects.get_or_create(product=p, rating=rating, text=text)

        self.stdout.write(self.style.SUCCESS(
            "✅ Seed data created/updated.\n"
            "Users: alice / bob / charlie (password123)\n"
            "Products created without images (upload via Admin later)."
        ))
