from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

from shop.models import Product, Review


class SmartShopAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="alice", password="password123")

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

        # Reviews for summarization endpoint
        Review.objects.create(product=cls.p1, rating=5, text="Great quality and works perfectly.")
        Review.objects.create(product=cls.p1, rating=4, text="Good value for money. I like it.")
        Review.objects.create(product=cls.p1, rating=2, text="Not durable.")

    # -------------------------
    # API: products list
    # -------------------------
    def test_api_products_returns_list(self):
        url = reverse("api_products")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(isinstance(data, list))
        self.assertTrue(any(p["name"] == "Wireless Earbuds" for p in data))

    # -------------------------
    # API: search (keyword)
    # -------------------------
    def test_api_search_keyword(self):
        url = reverse("api_search")
        resp = self.client.get(url, {"q": "earbuds"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("results", data)
        self.assertTrue(any(p["name"] == "Wireless Earbuds" for p in data["results"]))

    # -------------------------
    # API: search (under price)
    # -------------------------
    def test_api_search_under_price(self):
        url = reverse("api_search")
        resp = self.client.get(url, {"q": "under $20"})
        self.assertEqual(resp.status_code, 200)
        names = [p["name"] for p in resp.json()["results"]]
        self.assertIn("Yoga Mat", names)
        self.assertNotIn("Smart Watch", names)

    # -------------------------
    # API: search (above price)
    # -------------------------
    def test_api_search_above_price(self):
        url = reverse("api_search")
        resp = self.client.get(url, {"q": "above $60"})
        self.assertEqual(resp.status_code, 200)
        names = [p["name"] for p in resp.json()["results"]]
        self.assertIn("Smart Watch", names)
        self.assertNotIn("Yoga Mat", names)

    # -------------------------
    # API: chat (mock AI success)
    # -------------------------
    @patch("shop.views.generate_text", return_value="Mock AI reply: Wireless Earbuds ($49.90)")
    def test_api_chat_returns_reply(self, mock_ai):
        url = reverse("api_chat")
        resp = self.client.post(url, data={"message": "Suggest product below $50"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reply", data)
        self.assertTrue(len(data["reply"]) > 0)

    # -------------------------
    # API: chat (AI fails -> fallback must still reply)
    # -------------------------
    @patch("shop.views.generate_text", return_value="")
    def test_api_chat_fallback_reply_when_ai_empty(self, mock_ai):
        url = reverse("api_chat")
        resp = self.client.post(url, data={"message": "Most expensive products"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        reply = resp.json().get("reply", "")
        self.assertTrue(len(reply) > 0)
        # should include at least one product name from DB
        self.assertTrue("Smart Watch" in reply or "Wireless Earbuds" in reply or "Yoga Mat" in reply)

    # -------------------------
    # API: generate description (mock AI)
    # -------------------------
    @patch("shop.views.generate_text", return_value="AI Description: Great earbuds for gym use.")
    def test_generate_description_endpoint(self, mock_ai):
        url = reverse("api_generate_description", kwargs={"product_id": self.p1.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_description", data)
        self.assertIn("AI Description", data["ai_description"])

    # -------------------------
    # API: summarize reviews (mock AI)
    # -------------------------
    @patch("shop.views.generate_text", return_value="Summary: Mostly positive. Pros: quality. Cons: durability.")
    def test_summarize_reviews_endpoint(self, mock_ai):
        url = reverse("api_summarize_reviews", kwargs={"product_id": self.p1.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_review_summary", data)
        self.assertTrue(len(data["ai_review_summary"]) > 0)
