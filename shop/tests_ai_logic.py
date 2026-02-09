from django.test import TestCase
from unittest.mock import patch
from shop.models import Product

class SmartShopAILogicTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(name="Cheap Item", category="Home", price=10.00, tags="cheap,home")
        Product.objects.create(name="Mid Item", category="Home", price=50.00, tags="mid,home")
        Product.objects.create(name="Expensive Item", category="Home", price=200.00, tags="premium,home")

    @patch("shop.views.generate_text", return_value="")
    def test_chat_high_price_no_number_returns_expensive(self, mock_ai):
        # AI returns empty, so deterministic DB logic must still choose expensive items
        from django.urls import reverse
        from django.test import Client

        c = Client()
        resp = c.post(reverse("api_chat"), data={"message": "higher price products"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        reply = resp.json()["reply"]
        self.assertIn("Expensive Item", reply)

    @patch("shop.views.generate_text", return_value="")
    def test_chat_under_budget_returns_cheap(self, mock_ai):
        from django.urls import reverse
        from django.test import Client

        c = Client()
        resp = c.post(reverse("api_chat"), data={"message": "under $20"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        reply = resp.json()["reply"]
        self.assertIn("Cheap Item", reply)
        self.assertNotIn("Expensive Item", reply)

    @patch("shop.views.generate_text", return_value="")
    def test_chat_above_budget_returns_expensive(self, mock_ai):
        from django.urls import reverse
        from django.test import Client

        c = Client()
        resp = c.post(reverse("api_chat"), data={"message": "above $100"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        reply = resp.json()["reply"]
        self.assertIn("Expensive Item", reply)
