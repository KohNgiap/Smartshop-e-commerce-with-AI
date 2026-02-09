from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

from shop.models import Product, Review, Interaction


class SmartShopTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        cls.user = User.objects.create_user(username="alice", password="password123")

        # Create products (no image required)
        cls.p1 = Product.objects.create(
            name="Wireless Earbuds",
            category="Electronics",
            price=49.90,
            tags="audio,wireless,gym",
            short_description="Compact wireless earbuds."
        )
        cls.p2 = Product.objects.create(
            name="Yoga Mat",
            category="Sports",
            price=18.00,
            tags="fitness,yoga,home-workout",
            short_description="Non-slip yoga mat."
        )
        cls.p3 = Product.objects.create(
            name="Smart Watch",
            category="Electronics",
            price=119.00,
            tags="health,fitness,wearable",
            short_description="Track fitness and notifications."
        )

        # Reviews for p1
        Review.objects.create(product=cls.p1, rating=5, text="Great quality and works perfectly.")
        Review.objects.create(product=cls.p1, rating=4, text="Good value for money. I like it.")
        Review.objects.create(product=cls.p1, rating=3, text="It’s okay, but could be better.")
        Review.objects.create(product=cls.p1, rating=2, text="Not very durable. Disappointed.")

    # -------------------------
    # 1) Page tests (Django templates)
    # -------------------------
    def test_home_page_loads(self):
        url = reverse("home")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Product Catalog")

    def test_product_detail_page_loads(self):
        url = reverse("product_detail", kwargs={"product_id": self.p1.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.p1.name)

    # -------------------------
    # 2) API search tests
    # -------------------------
    def test_api_search_keyword(self):
        url = reverse("api_search")
        resp = self.client.get(url, {"q": "earbuds"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertTrue(any(item["name"] == "Wireless Earbuds" for item in data["results"]))

    def test_api_search_under_price(self):
        url = reverse("api_search")
        resp = self.client.get(url, {"q": "under $20"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        names = [p["name"] for p in data["results"]]
        self.assertIn("Yoga Mat", names)          # 18.00 should match
        self.assertNotIn("Smart Watch", names)    # 119 should NOT match

    def test_api_search_above_price(self):
        url = reverse("api_search")
        resp = self.client.get(url, {"q": "above $60"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        names = [p["name"] for p in data["results"]]
        self.assertIn("Smart Watch", names)
        self.assertNotIn("Yoga Mat", names)

    # -------------------------
    # 3) Chat API test (mock AI)
    # -------------------------
    @patch("shop.views.generate_text", return_value="Here are some products under $50: Wireless Earbuds ($49.90)")
    def test_api_chat_returns_reply(self, mock_ai):
        url = reverse("api_chat")
        resp = self.client.post(url, data={"message": "Suggest product below $50"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reply", data)
        self.assertTrue(len(data["reply"]) > 0)

    # -------------------------
    # 4) Generate description API test (mock AI)
    # -------------------------
    @patch("shop.views.generate_text", return_value="AI Description: A compact wireless earbuds for daily use.")
    def test_api_generate_description(self, mock_ai):
        url = reverse("api_generate_description", kwargs={"product_id": self.p1.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_description", data)
        self.assertIn("AI Description", data["ai_description"])

        # Confirm saved into DB
        self.p1.refresh_from_db()
        self.assertTrue("AI Description" in (self.p1.ai_description or ""))

    # -------------------------
    # 5) Summarize reviews API test (mock AI)
    # -------------------------
    @patch("shop.views.generate_text", return_value="Overall sentiment: Positive. Pros: good value. Cons: durability.")
    def test_api_summarize_reviews(self, mock_ai):
        url = reverse("api_summarize_reviews", kwargs={"product_id": self.p1.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_review_summary", data)
        self.assertTrue(len(data["ai_review_summary"]) > 0)

        # Confirm saved into DB
        self.p1.refresh_from_db()
        self.assertTrue(len(self.p1.ai_review_summary or "") > 0)

    # -------------------------
    # 6) Verify interaction logging works (optional)
    # -------------------------
    def test_search_logs_interaction_when_logged_in(self):
        self.client.login(username="alice", password="password123")
        url = reverse("api_search")
        self.client.get(url, {"q": "earbuds"})
        self.assertTrue(Interaction.objects.filter(user=self.user, event_type="SEARCH").exists())
