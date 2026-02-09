from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Interaction, Review
from .serializers import ProductSerializer
from .services.gemini_client import generate_text, generate_json

def basic_review_summary(reviews):
    """
    Fallback summarizer (no AI):
    - average rating
    - simple pros/cons from keywords
    This is great for assignment evidence if AI quota is exhausted.
    """
    if not reviews:
        return "No reviews yet."

    avg = sum(r.rating for r in reviews) / len(reviews)

    pros_keywords = ["great", "good", "perfect", "love", "value", "works", "quality"]
    cons_keywords = ["bad", "poor", "disappointed", "durable", "worse", "problem", "okay"]

    pros = []
    cons = []

    for r in reviews:
        t = (r.text or "").lower()
        if any(k in t for k in pros_keywords):
            pros.append(r.text)
        if any(k in t for k in cons_keywords):
            cons.append(r.text)

    pros = pros[:3] if pros else ["No strong pros detected from text."]
    cons = cons[:3] if cons else ["No strong cons detected from text."]

    summary = []
    summary.append(f"Overall sentiment: average rating is {avg:.1f}/5 from {len(reviews)} review(s).")
    summary.append("")
    summary.append("Top pros:")
    for p in pros:
        summary.append(f"- {p}")
    summary.append("")
    summary.append("Top cons:")
    for c in cons:
        summary.append(f"- {c}")

    return "\n".join(summary)



# -----------------------
# UI PAGES (MTV templates)
# -----------------------
def home(request):
    products = Product.objects.all().order_by("id")[:24]

    recommended = []
    if request.user.is_authenticated:
        recommended = _recommend_products_for_user(request.user)[:8]

    return render(
        request,
        "shop/home.html",
        {"products": products, "recommended": recommended},
    )

def product_detail(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)

    # Log a VIEW interaction (simulates behavior tracking)
    if request.user.is_authenticated:
        Interaction.objects.create(user=request.user, product=product, event_type="VIEW")

    reviews = product.reviews.all().order_by("-created_at")[:10]
    return render(
        request,
        "shop/product_detail.html",
        {"product": product, "reviews": reviews},
    )


# -----------------------
# RECOMMENDATION ENGINE
# -----------------------
def _recommend_products_for_user(user: User):
    """
    Algorithm/Logic (good for your report):
    1) Collect user interactions (VIEW/CART/PURCHASE/SEARCH)
    2) Build a small user profile summary
    3) Ask Gemini to rank products from the catalog based on the profile
    4) Return ranked Product queryset/list
    """
    # Last 50 interactions
    interactions = Interaction.objects.filter(user=user).order_by("-created_at")[:50]

    # If no history, fallback: popular products by purchase count
    if not interactions.exists():
        popular_ids = (
            Interaction.objects.filter(event_type="PURCHASE", product__isnull=False)
            .values("product_id")
            .annotate(c=Count("product_id"))
            .order_by("-c")[:10]
        )
        ids = [x["product_id"] for x in popular_ids if x["product_id"]]
        if not ids:
            return list(Product.objects.all()[:10])
        return list(Product.objects.filter(id__in=ids))

    # Build user signals
    viewed = [i.product.name for i in interactions if i.event_type == "VIEW" and i.product]
    purchased = [i.product.name for i in interactions if i.event_type == "PURCHASE" and i.product]
    searched = [i.query_text for i in interactions if i.event_type == "SEARCH" and i.query_text]

    # Candidate catalog (limit for prompt size)
    catalog = list(Product.objects.all()[:50])
    catalog_lines = []
    for p in catalog:
        catalog_lines.append(
            f"{p.id}. {p.name} | category={p.category} | price={p.price} | tags={p.tags}"
        )

    prompt = f"""
You are an e-commerce recommendation engine.
Return ONLY valid JSON (no markdown, no explanation).

User behavior:
- viewed: {viewed[-10:]}
- purchased: {purchased[-10:]}
- searched: {searched[-10:]}

Task:
Rank the best product IDs from this catalog for the user.

Catalog:
{chr(10).join(catalog_lines)}

Return JSON in this format:
{{
  "recommended_product_ids": [1,2,3,4,5,6,7,8]
}}
"""

    data = generate_json(prompt)
    ids = data.get("recommended_product_ids", [])

    # Validate IDs exist in catalog
    ids = [i for i in ids if isinstance(i, int)]
    found = list(Product.objects.filter(id__in=ids))

    # Keep Gemini order
    found_map = {p.id: p for p in found}
    ordered = [found_map[i] for i in ids if i in found_map]

    # Fallback if Gemini fails
    if not ordered:
        return list(Product.objects.all()[:10])

    return ordered


# -----------------------
# REST API ENDPOINTS
# -----------------------
@api_view(["GET"])
def api_products(request):
    qs = Product.objects.all().order_by("id")
    return Response(ProductSerializer(qs, many=True).data)

@api_view(["GET"])
def api_search(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return Response({"results": []})

    # Log SEARCH for authenticated users
    if request.user.is_authenticated:
        Interaction.objects.create(user=request.user, event_type="SEARCH", query_text=q)

    # Simple NLP-ish keyword search (baseline)
    qs = Product.objects.filter(
        Q(name__icontains=q) | Q(category__icontains=q) | Q(tags__icontains=q)
    ).order_by("id")[:20]

    return Response({"results": ProductSerializer(qs, many=True).data})

@api_view(["GET"])
def api_recommendations(request, username: str):
    user = get_object_or_404(User, username=username)
    products = _recommend_products_for_user(user)
    return Response({"user": user.username, "recommendations": ProductSerializer(products, many=True).data})

@api_view(["POST"])
def api_generate_description(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)

    prompt = f"""
Write a short, engaging e-commerce product description (80-120 words).
Focus on benefits, not only specs.
Product:
- name: {product.name}
- category: {product.category}
- price: {product.price}
- tags: {product.tags}
Existing short description: {product.short_description}
"""
    text = generate_text(prompt)
    if not text:
        return Response({"error": "Gemini returned empty text"}, status=status.HTTP_502_BAD_GATEWAY)

    product.ai_description = text
    product.save()
    return Response({"product_id": product.id, "ai_description": product.ai_description})

@api_view(["POST"])
def api_summarize_reviews(request, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    reviews = list(product.reviews.all().order_by("-created_at")[:20])

    if not reviews:
        return Response(
            {"error": "No reviews available to summarize."},
            status=status.HTTP_400_BAD_REQUEST
        )

    review_text = "\n".join([f"- ({r.rating}/5) {r.text}" for r in reviews])

    prompt = f"""
Summarize these customer reviews into:
1) Overall sentiment (one sentence)
2) Top pros (bullet points)
3) Top cons (bullet points)

Reviews:
{review_text}
"""

    summary = generate_text(prompt)

    if not summary:
        return Response(
            {"error": "AI service unavailable. Please try again later."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    product.ai_review_summary = summary
    product.save()

    return Response({
        "product_id": product.id,
        "ai_review_summary": product.ai_review_summary
    })

@api_view(["POST"])
def api_chat(request):
    """
    Virtual shopping assistant.
    Request JSON:
    { "message": "..." }
    """
    msg = (request.data.get("message") or "").strip()
    if not msg:
        return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Include some catalog context (small)
    catalog = list(Product.objects.all()[:20])
    catalog_text = "\n".join([f"- {p.name} (category={p.category}, price={p.price})" for p in catalog])

    prompt = f"""
You are SmartShop's virtual shopping assistant.
Be helpful, short, and friendly.
If user asks for product suggestions, recommend items from this catalog only.

Catalog:
{catalog_text}

User message: {msg}
"""
    reply = generate_text(prompt)
    if not reply:
        reply = "Sorry — I couldn't generate a response right now. Please try again."

    return Response({"reply": reply})
