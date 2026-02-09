from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from shop.models import Product, Review


class BackendAIIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.p = Product.objects.create(
            name="Wireless Earbuds",
            category="Electronics",
            price=49.90,
            tags="audio,wireless,gym",
            short_description="Compact earbuds"
        )
        Review.objects.create(product=cls.p, rating=5, text="Great product, works well.")
        Review.objects.create(product=cls.p, rating=4, text="Good value for money.")

    @patch("shop.views.generate_text", return_value="AI Description: Great earbuds for daily use.")
    def test_generate_description_end_to_end(self, mock_ai):
        url = reverse("api_generate_description", kwargs={"product_id": self.p.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_description", data)
        self.assertIn("AI Description", data["ai_description"])

    @patch("shop.views.generate_text", return_value="Summary: Positive. Pros: good sound. Cons: none.")
    def test_summarize_reviews_end_to_end(self, mock_ai):
        url = reverse("api_summarize_reviews", kwargs={"product_id": self.p.id})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ai_review_summary", data)
        self.assertTrue(len(data["ai_review_summary"]) > 0)

    @patch("shop.views.generate_text", return_value="")
    def test_chat_fallback_end_to_end_when_ai_empty(self, mock_ai):
        url = reverse("api_chat")
        resp = self.client.post(url, data={"message": "most expensive products"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        reply = resp.json().get("reply", "")
        self.assertTrue(len(reply) > 0)
        # must include at least one real product
        self.assertIn("Wireless Earbuds", reply)
