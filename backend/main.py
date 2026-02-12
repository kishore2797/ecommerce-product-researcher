from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import uuid
import time
import re
import math
import csv
import io
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="E-Commerce Product Researcher Agent API",
    description="Multi-Agent + RAG + MCP — Automates competitor & trend research for online sellers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# ─── In-Memory Stores ────────────────────────────────────────
sales_data: List[Dict[str, Any]] = []
product_research: List[Dict[str, Any]] = []
competitors_store: List[Dict[str, Any]] = []
chat_sessions: Dict[str, List[Dict[str, Any]]] = {}
uploaded_files: List[Dict[str, Any]] = []
analytics: Dict[str, Any] = {
    "total_queries": 0,
    "queries_by_type": {},
    "avg_response_time": 0,
    "total_response_time": 0,
    "feedback_positive": 0,
    "feedback_negative": 0,
    "files_uploaded": 0,
    "products_researched": 0,
    "reports_generated": 0,
}

PRODUCT_NICHES = [
    "Home & Kitchen", "Beauty & Personal Care", "Health & Wellness",
    "Pet Supplies", "Baby & Kids", "Outdoor & Garden",
    "Electronics & Gadgets", "Fitness & Sports", "Automotive",
    "Office & Productivity", "Fashion & Accessories", "Toys & Games",
]

# ─── E-Commerce Knowledge Base (RAG corpus) ──────────────────
ECOMMERCE_KNOWLEDGE = [
    {
        "id": "kb-trends-001", "title": "Trend Analysis Fundamentals", "category": "trends",
        "sections": [
            {"section": "Identifying Winning Products", "page": 1,
             "content": "A winning e-commerce product exhibits: rising Google Trends search volume (>50% increase over 30 days), low competition density (<30 sellers), healthy margin potential (>35% after COGS, shipping, ad spend), strong visual appeal for social media ads, and solves a clear pain point. Avoid products with flat trends, heavy brand dominance, or margins <20%. The ideal product has a 2-4 week trend acceleration window."},
            {"section": "Seasonal Trend Patterns", "page": 2,
             "content": "E-commerce follows seasonal cycles: Q1 — fitness, organization, Valentine's. Q2 — outdoor, garden, graduation. Q3 — back-to-school, fall fashion. Q4 — holiday gifts, Black Friday, winter gear. Source 6-8 weeks before peak. Products with year-round demand plus seasonal spikes are lower risk than pure seasonal items."},
            {"section": "TikTok-to-Amazon Pipeline", "page": 3,
             "content": "Modern product discovery: TikTok viral → Google search spike → Amazon sales surge within 5-10 days. Monitor #TikTokMadeMeBuyIt, creator reviews with >100K views. Window from virality to saturation is 3-6 weeks. Validate on Google Trends, check Amazon competition, source quickly."},
        ],
    },
    {
        "id": "kb-competition-001", "title": "Competitive Analysis Guide", "category": "competition",
        "sections": [
            {"section": "Amazon Competition Assessment", "page": 5,
             "content": "Evaluate Amazon competition: sellers on page 1 (ideal <15), avg review count of top 10 (ideal <500), review quality gap (3-star averages = opportunity), BSR trend, price clustering, listing quality. Use Review Sentiment Gap strategy: analyze 1-2 star reviews to find common complaints, then source a product that fixes those issues."},
            {"section": "Pricing Strategy Framework", "page": 7,
             "content": "Pricing approaches: Cost-plus (2.5-3x landed cost for dropshipping), Competitive positioning (within 10% of leader), Perceived value (premium branding justifies 20-40% premium). The Goldilocks Zone is $25-$75 — high enough for margins, low enough for impulse buys. Below $15 margins are too thin; above $100 conversion drops."},
        ],
    },
    {
        "id": "kb-sourcing-001", "title": "Product Sourcing Guide", "category": "sourcing",
        "sections": [
            {"section": "Supplier Evaluation Criteria", "page": 10,
             "content": "Evaluate suppliers on: response time (<24h), MOQ flexibility (100-500 units), sample quality, production capacity (5000+ units/mo), certifications (UL, CE, FDA), communication quality, payment terms (Trade Assurance or 30/70 split). Red flags: no factory photos, won't send samples, prices far below market."},
            {"section": "US Warehouse Fulfillment", "page": 11,
             "content": "For competitive shipping: Amazon FBA (2-day Prime, $5-8/unit), 3PL (ShipBob, Deliverr — 3-5 day, $3-6/unit), supplier US warehouses. 2-day shipping converts 2-3x better than 7-14 day. Landed cost = product + shipping to warehouse + warehouse fees + pick/pack + last-mile."},
        ],
    },
    {
        "id": "kb-advertising-001", "title": "E-Commerce Advertising Guide", "category": "advertising",
        "sections": [
            {"section": "Facebook/Meta Ads Strategy", "page": 14,
             "content": "Launch strategy: $20-50/day across 3-5 ad sets. Broad targeting initially. UGC videos outperform polished ads by 30-50%. Test 3 hooks in first 3 seconds. Key metrics: CTR >1.5%, CPC <$1.50, ROAS >2.0x. Scale winners 20% every 48h. Kill underperformers after $20-30 with no purchases."},
            {"section": "Amazon PPC Fundamentals", "page": 15,
             "content": "Start with Automatic campaigns ($10-20/day). After 2 weeks, harvest keywords into Manual Exact Match. Target ACoS 25-35% during launch, 15-20% at maturity. Sponsored Products drive 80% of PPC revenue. Target TACoS <12% for healthy business."},
        ],
    },
    {
        "id": "kb-metrics-001", "title": "E-Commerce Business Metrics", "category": "metrics",
        "sections": [
            {"section": "Unit Economics Calculator", "page": 18,
             "content": "Healthy unit economics: Price - COGS (25-35%) - Fulfillment (10-15%) - Platform Fees (Amazon 15%, Shopify 2.9%+$0.30) - Ads (20-30% growth, 10-15% maturity) = Net Profit (15-25% target). Track CAC, LTV, LTV:CAC ratio (target >3:1). Products with <20% net margin are not sustainable."},
            {"section": "Product Scoring Model", "page": 19,
             "content": "Score on 7 dimensions (0-100): Trend Velocity (20%), Competition Density (18% inverted), Margin Potential (20%), Shipping Feasibility (12%), Review Sentiment Gap (10%), Seasonality Risk (10% inverted), Ad Creative Potential (10%). Composite = weighted average. Products >75 are strong candidates."},
        ],
    },
]

# ─── Mock Google Trends Data (simulates MCP) ─────────────────
def generate_mock_trends(niche: str, days: int = 30) -> Dict:
    random.seed(hash(niche) % 10000)
    base_interest = random.randint(30, 70)
    trend_data = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        noise = random.randint(-8, 12)
        growth = int(i * random.uniform(0.3, 1.5))
        value = min(100, max(0, base_interest + growth + noise))
        trend_data.append({"date": date, "interest": value})

    query_pool = {
        "Home & Kitchen": ["portable ice maker", "self watering planter", "led closet light", "collapsible colander", "smart soap dispenser", "bamboo desk organizer", "magnetic spice rack", "electric kettle gooseneck"],
        "Beauty & Personal Care": ["ice roller face", "scalp massager", "led face mask", "hair oil serum", "vitamin c serum", "jade roller set", "lip sleeping mask", "retinol cream"],
        "Health & Wellness": ["posture corrector", "massage gun mini", "blue light glasses", "sleep gummies", "protein shaker", "resistance bands set", "acupressure mat", "neck stretcher"],
        "Pet Supplies": ["automatic cat feeder", "dog cooling mat", "pet water fountain", "calming dog bed", "cat tree tower", "dog paw cleaner", "pet camera treat", "slow feeder bowl"],
        "Electronics & Gadgets": ["magnetic phone mount", "portable monitor", "wireless earbuds", "mini projector", "smart plug wifi", "ring light desk", "cable organizer", "power bank solar"],
        "Fitness & Sports": ["walking pad treadmill", "adjustable dumbbells", "yoga mat thick", "jump rope weighted", "foam roller set", "pull up bar door", "ab roller wheel", "grip strength trainer"],
    }
    queries = query_pool.get(niche, [f"trending product {i}" for i in range(1, 9)])
    rising_queries = []
    for q in queries[:6]:
        rising_queries.append({"query": q, "search_volume": random.randint(5000, 80000), "growth_pct": random.randint(15, 350), "trend": random.choice(["rising", "rising", "rising", "breakout"])})
    rising_queries.sort(key=lambda x: x["growth_pct"], reverse=True)

    current = trend_data[-1]["interest"] if trend_data else 50
    previous = trend_data[0]["interest"] if trend_data else 50
    velocity = round((current - previous) / max(previous, 1) * 100, 1)

    return {
        "niche": niche, "period": f"Last {days} days", "current_interest": current,
        "trend_velocity": velocity,
        "trend_direction": "rising" if velocity > 10 else "stable" if velocity > -10 else "declining",
        "interest_over_time": trend_data, "rising_queries": rising_queries,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": "Google Trends API (demo)",
    }


# ─── Mock Amazon Product Data (simulates MCP) ────────────────
def generate_mock_amazon_products(niche: str, count: int = 10) -> List[Dict]:
    random.seed(hash(niche + "amazon") % 10000)
    templates = {
        "Home & Kitchen": [
            ("Portable Countertop Ice Maker", 79.99, 129.99), ("Self-Watering Planter System (3-Pack)", 24.99, 44.99),
            ("LED Motion Sensor Closet Light (2-Pack)", 14.99, 29.99), ("Collapsible Silicone Kitchen Colander Set", 12.99, 24.99),
            ("Touchless Automatic Soap Dispenser", 19.99, 39.99), ("Bamboo Desktop Organizer with Drawers", 29.99, 54.99),
            ("Magnetic Spice Rack for Refrigerator", 22.99, 42.99), ("Electric Gooseneck Kettle Temperature Control", 39.99, 69.99),
            ("Silicone Stretch Lids (14-Pack)", 9.99, 18.99), ("Under Cabinet LED Strip Light Kit", 16.99, 34.99),
        ],
        "Beauty & Personal Care": [
            ("Ice Roller for Face & Eyes", 8.99, 19.99), ("Scalp Massager Shampoo Brush", 7.99, 14.99),
            ("LED Light Therapy Face Mask", 39.99, 89.99), ("Rosemary Hair Growth Oil Serum", 12.99, 24.99),
            ("Vitamin C Brightening Serum", 14.99, 29.99), ("Jade Roller & Gua Sha Set", 11.99, 24.99),
            ("Lip Sleeping Mask Berry", 9.99, 22.99), ("Retinol Anti-Aging Night Cream", 18.99, 39.99),
            ("Silk Pillowcase for Hair & Skin", 14.99, 29.99), ("Makeup Brush Cleaner Electric", 16.99, 34.99),
        ],
        "Health & Wellness": [
            ("Posture Corrector Back Brace", 19.99, 34.99), ("Mini Massage Gun Portable", 34.99, 69.99),
            ("Blue Light Blocking Glasses (2-Pack)", 14.99, 24.99), ("Melatonin Sleep Gummies (60ct)", 12.99, 22.99),
            ("Protein Shaker Bottle Electric", 24.99, 44.99), ("Resistance Bands Set (5-Pack)", 11.99, 24.99),
            ("Acupressure Mat and Pillow Set", 29.99, 49.99), ("Neck & Shoulder Stretcher", 19.99, 34.99),
            ("Digital Food Scale Kitchen", 12.99, 24.99), ("Wrist Blood Pressure Monitor", 29.99, 54.99),
        ],
        "Pet Supplies": [
            ("Automatic Cat Feeder WiFi", 49.99, 89.99), ("Dog Cooling Mat Large", 19.99, 39.99),
            ("Pet Water Fountain Stainless", 24.99, 44.99), ("Calming Dog Bed Donut", 29.99, 54.99),
            ("Cat Tree Tower 5-Level", 49.99, 99.99), ("Dog Paw Cleaner Portable", 12.99, 24.99),
            ("Pet Camera with Treat Dispenser", 39.99, 79.99), ("Slow Feeder Dog Bowl", 9.99, 19.99),
            ("Cat Scratcher Cardboard Lounge", 14.99, 29.99), ("Dog Seat Belt Harness", 12.99, 22.99),
        ],
        "Electronics & Gadgets": [
            ("Magnetic Car Phone Mount", 12.99, 24.99), ("Portable Monitor 15.6 inch", 129.99, 199.99),
            ("Wireless Earbuds ANC", 29.99, 59.99), ("Mini Projector 1080P", 69.99, 129.99),
            ("Smart Plug WiFi (4-Pack)", 19.99, 34.99), ("Ring Light 10 inch Desk", 19.99, 39.99),
            ("Cable Organizer Box", 14.99, 24.99), ("Solar Power Bank 20000mAh", 24.99, 44.99),
            ("USB-C Hub 7-in-1", 19.99, 39.99), ("Webcam 1080P with Mic", 24.99, 49.99),
        ],
        "Fitness & Sports": [
            ("Walking Pad Under Desk Treadmill", 199.99, 299.99), ("Adjustable Dumbbells 25lb Pair", 79.99, 149.99),
            ("Yoga Mat Extra Thick 6mm", 19.99, 34.99), ("Weighted Jump Rope", 14.99, 29.99),
            ("Foam Roller Set 3-Pack", 19.99, 34.99), ("Pull Up Bar Doorway", 24.99, 44.99),
            ("Ab Roller Wheel Kit", 14.99, 29.99), ("Grip Strength Trainer Set", 12.99, 24.99),
            ("Massage Ball Set", 9.99, 19.99), ("Workout Gloves Ventilated", 14.99, 24.99),
        ],
    }
    product_list = templates.get(niche, [(f"{niche} Product {i}", 14.99 + i * 5, 29.99 + i * 8) for i in range(1, 11)])
    products = []
    for name, low, high in product_list[:count]:
        price = round(random.uniform(low, high), 2)
        bsr = random.randint(800, 85000)
        products.append({
            "asin": f"B0{random.randint(10000000, 99999999)}", "title": name, "price": price,
            "rating": round(random.uniform(3.2, 4.9), 1), "review_count": random.randint(12, 4500),
            "bsr": bsr, "bsr_category": niche,
            "estimated_monthly_sales": max(50, int(200000 / bsr * random.uniform(0.6, 1.4))),
            "estimated_monthly_revenue": round(max(50, int(200000 / bsr * random.uniform(0.6, 1.4))) * price, 2),
            "seller_count": random.randint(3, 45),
            "fba_available": random.choice([True, True, True, False]),
            "prime_eligible": random.choice([True, True, False]),
        })
    products.sort(key=lambda x: x["bsr"])
    return products


# ─── Mock Competitor Data ─────────────────────────────────────
def generate_mock_competitors(product_name: str) -> List[Dict]:
    random.seed(hash(product_name + "comp") % 10000)
    store_names = ["ArcticCool Co.", "PrimeLiving Store", "HomeEssentials Pro", "SmartHome Direct",
                   "EverydayDeals Shop", "QualityFirst Goods", "TrendyFinds", "ValueMax Store", "PremiumPicks", "BudgetSmart"]
    comps = []
    for i in range(random.randint(5, 10)):
        comps.append({
            "id": str(uuid.uuid4()), "store_name": store_names[i % len(store_names)],
            "platform": random.choice(["Amazon", "Amazon", "Amazon", "Shopify", "Shopify", "Walmart"]),
            "price": round(random.uniform(19.99, 129.99), 2),
            "rating": round(random.uniform(3.0, 4.9), 1), "review_count": random.randint(15, 5000),
            "estimated_monthly_sales": random.randint(100, 5000),
            "shipping_speed": random.choice(["2-day (Prime)", "3-5 days", "5-7 days", "7-14 days"]),
            "estimated_ad_spend": round(random.uniform(1000, 15000), 0) if random.random() > 0.3 else None,
            "strengths": random.sample(["Strong brand", "Fast shipping", "High reviews", "Competitive pricing", "Premium packaging", "Active social media"], k=random.randint(1, 3)),
            "weaknesses": random.sample(["Slow shipping", "Low reviews", "Poor photos", "High price", "No social media", "Bad sentiment"], k=random.randint(1, 3)),
        })
    comps.sort(key=lambda x: x["estimated_monthly_sales"], reverse=True)
    return comps


# ─── Product Scoring Engine ──────────────────────────────────
def score_product(product: Dict, trends: Dict, comp_list: List[Dict]) -> Dict:
    random.seed(hash(product.get("title", "")) % 10000)
    velocity = trends.get("trend_velocity", 0)
    trend_score = min(100, max(0, int(50 + velocity * 1.5)))
    seller_count = product.get("seller_count", 20)
    avg_reviews = sum(c.get("review_count", 0) for c in comp_list) / max(len(comp_list), 1)
    competition_score = max(0, int(100 - min(100, seller_count * 2 + avg_reviews / 50)))
    price = product.get("price", 50)
    est_cost = price * random.uniform(0.2, 0.4)
    est_ad = price * random.uniform(0.15, 0.3)
    margin_pct = (price - est_cost - est_ad) / price * 100
    margin_score = min(100, max(0, int(margin_pct * 1.5)))
    shipping_score = 85 if product.get("fba_available", False) else random.randint(40, 70)
    sentiment_gap_score = min(100, max(0, int((5.0 - product.get("rating", 4.0)) * 40 + random.randint(10, 30))))
    seasonality_score = random.randint(50, 90)
    creative_score = random.randint(55, 95)
    composite = round(trend_score * 0.20 + competition_score * 0.18 + margin_score * 0.20 + shipping_score * 0.12 + sentiment_gap_score * 0.10 + seasonality_score * 0.10 + creative_score * 0.10, 1)
    confidence = 5 if composite >= 80 else 4 if composite >= 65 else 3 if composite >= 50 else 2
    return {
        "composite_score": composite, "confidence": confidence,
        "dimensions": {
            "trend_velocity": {"score": trend_score, "weight": "20%"},
            "competition_density": {"score": competition_score, "weight": "18%"},
            "margin_potential": {"score": margin_score, "weight": "20%"},
            "shipping_feasibility": {"score": shipping_score, "weight": "12%"},
            "review_sentiment_gap": {"score": sentiment_gap_score, "weight": "10%"},
            "seasonality_risk": {"score": seasonality_score, "weight": "10%"},
            "ad_creative_potential": {"score": creative_score, "weight": "10%"},
        },
        "estimated_margin_pct": round(margin_pct, 1), "estimated_landed_cost": round(est_cost, 2),
        "estimated_ad_cost_per_unit": round(est_ad, 2),
    }


# ─── Sample Data Generators ──────────────────────────────────
def generate_sample_sales():
    samples = []
    random.seed(42)
    base_date = datetime(2024, 1, 1)
    catalog = [
        {"name": "Bamboo Cutting Board Set", "cat": "Home & Kitchen", "price": 34.99, "cost": 9.50},
        {"name": "LED Desk Lamp Touch Control", "cat": "Home & Kitchen", "price": 29.99, "cost": 8.20},
        {"name": "Silicone Baking Mat (3-Pack)", "cat": "Home & Kitchen", "price": 14.99, "cost": 3.80},
        {"name": "Portable Blender USB", "cat": "Home & Kitchen", "price": 24.99, "cost": 7.50},
        {"name": "Resistance Bands Set", "cat": "Fitness & Sports", "price": 19.99, "cost": 4.20},
        {"name": "Yoga Mat Extra Thick", "cat": "Fitness & Sports", "price": 29.99, "cost": 7.80},
        {"name": "Ice Roller Face Massager", "cat": "Beauty & Personal Care", "price": 12.99, "cost": 2.40},
        {"name": "Vitamin C Serum", "cat": "Beauty & Personal Care", "price": 16.99, "cost": 3.60},
        {"name": "Dog Paw Cleaner Cup", "cat": "Pet Supplies", "price": 14.99, "cost": 3.20},
        {"name": "Cat Water Fountain", "cat": "Pet Supplies", "price": 24.99, "cost": 6.80},
        {"name": "Wireless Earbuds Budget", "cat": "Electronics & Gadgets", "price": 19.99, "cost": 5.50},
        {"name": "Phone Stand Adjustable", "cat": "Electronics & Gadgets", "price": 12.99, "cost": 2.80},
    ]
    stores = ["Main Shopify Store", "Niche Store #2", "Amazon FBA", "Niche Store #3"]
    for mo in range(12):
        ms = base_date + timedelta(days=mo * 30)
        mn = ms.month
        seasonal = 1.8 if mn in [11, 12] else 1.2 if mn in [6, 7, 8] else 0.8 if mn in [1, 2] else 1.0
        for prod in catalog:
            for day in range(30):
                if random.random() > 0.3:
                    date = ms + timedelta(days=day)
                    qty = random.randint(1, max(1, int(random.uniform(3, 25) * seasonal) // 5))
                    rev = round(prod["price"] * qty, 2)
                    cost = round(prod["cost"] * qty, 2)
                    ad = round(rev * random.uniform(0.10, 0.30), 2)
                    fee = round(rev * random.uniform(0.03, 0.15), 2)
                    profit = round(rev - cost - ad - fee, 2)
                    samples.append({
                        "id": str(uuid.uuid4()), "date": date.strftime("%Y-%m-%d"),
                        "product_name": prod["name"], "category": prod["cat"],
                        "store": random.choice(stores), "quantity": qty,
                        "revenue": rev, "cost": cost, "ad_spend": ad, "platform_fee": fee,
                        "profit": profit, "margin_pct": round(profit / rev * 100, 1) if rev > 0 else 0,
                        "source": "sample",
                    })
    samples.sort(key=lambda x: x["date"])
    return samples


def generate_sample_research():
    random.seed(99)
    past = [
        {"name": "Portable Smoothie Maker", "niche": "Home & Kitchen", "outcome": "failed", "reason": "8.4% return rate due to battery issues.", "margin": 18.5, "months": 2},
        {"name": "Bamboo Cutting Board Set", "niche": "Home & Kitchen", "outcome": "winner", "reason": "Consistent demand, low returns, great reviews.", "margin": 42.3, "months": 14},
        {"name": "LED Desk Lamp Touch", "niche": "Home & Kitchen", "outcome": "winner", "reason": "Strong Q4 gifting demand. Good margin.", "margin": 38.7, "months": 11},
        {"name": "Fidget Spinner Deluxe", "niche": "Toys & Games", "outcome": "failed", "reason": "Trend died in 3 weeks. $4,200 unsold inventory.", "margin": -12.0, "months": 1},
        {"name": "Resistance Bands Set", "niche": "Fitness & Sports", "outcome": "winner", "reason": "Year-round demand with January spike.", "margin": 55.2, "months": 10},
        {"name": "Phone Grip Ring Holder", "niche": "Electronics & Gadgets", "outcome": "breakeven", "reason": "Too much competition. Price race to bottom.", "margin": 8.3, "months": 4},
        {"name": "Dog Paw Cleaner Cup", "niche": "Pet Supplies", "outcome": "winner", "reason": "Viral TikTok drove initial sales. Strong repeats.", "margin": 48.1, "months": 9},
        {"name": "Countertop Blender Pro", "niche": "Home & Kitchen", "outcome": "winner", "reason": "2,400 units/mo at $67.99.", "margin": 22.0, "months": 8},
        {"name": "UV Phone Sanitizer", "niche": "Electronics & Gadgets", "outcome": "failed", "reason": "COVID trend faded. Demand dropped 80%.", "margin": 5.2, "months": 3},
        {"name": "Self-Watering Planter", "niche": "Home & Kitchen", "outcome": "failed", "reason": "3.2% return rate due to leaking.", "margin": 15.4, "months": 3},
    ]
    records = []
    for p in past:
        records.append({
            "id": str(uuid.uuid4()),
            "date_researched": (datetime.now() - timedelta(days=random.randint(30, 500))).strftime("%Y-%m-%d"),
            "product_name": p["name"], "niche": p["niche"], "outcome": p["outcome"],
            "reason": p["reason"], "margin_pct": p["margin"], "months_active": p["months"],
            "revenue_total": round(random.uniform(2000, 180000), 2) if p["outcome"] == "winner" else round(random.uniform(500, 15000), 2),
        })
    return records


# ─── RAG Retrieval ────────────────────────────────────────────
knowledge_chunks: List[Dict[str, Any]] = []


def initialize_knowledge_base():
    for doc in ECOMMERCE_KNOWLEDGE:
        for i, section in enumerate(doc["sections"]):
            knowledge_chunks.append({
                "id": str(uuid.uuid4()), "document_id": doc["id"], "chunk_index": i,
                "text": section["content"], "section": section["section"],
                "page": section.get("page"), "category": doc["category"], "title": doc["title"],
            })


def text_to_vector(text: str) -> Counter:
    return Counter(re.findall(r'\w+', text.lower()))


def cosine_sim(v1: Counter, v2: Counter) -> float:
    inter = set(v1.keys()) & set(v2.keys())
    num = sum(v1[x] * v2[x] for x in inter)
    d1 = math.sqrt(sum(v1[x] ** 2 for x in v1))
    d2 = math.sqrt(sum(v2[x] ** 2 for x in v2))
    return num / (d1 * d2) if d1 * d2 else 0.0


def retrieve_chunks(query: str, top_k: int = 3) -> List[Dict]:
    qv = text_to_vector(query)
    scored = [(cosine_sim(qv, text_to_vector(c["text"])), c) for c in knowledge_chunks]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{**c, "relevance_score": round(s, 4)} for s, c in scored[:top_k] if s > 0.05]


def retrieve_research(query: str, top_k: int = 3) -> List[Dict]:
    qv = text_to_vector(query)
    scored = [(cosine_sim(qv, text_to_vector(f"{r['product_name']} {r['niche']} {r['outcome']} {r['reason']}")), r) for r in product_research]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for s, r in scored[:top_k] if s > 0.05]


# ─── Agent Tools ─────────────────────────────────────────────
def tool_search_trends(niche: str = "Home & Kitchen") -> Dict:
    return generate_mock_trends(niche)


def tool_search_amazon(niche: str = "Home & Kitchen", count: int = 10) -> Dict:
    products = generate_mock_amazon_products(niche, count)
    return {"niche": niche, "total_products": len(products), "products": products, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": "Amazon Product API (demo)"}


def tool_analyze_competitors(product_name: str) -> Dict:
    comps = generate_mock_competitors(product_name)
    return {
        "product": product_name, "total_competitors": len(comps),
        "avg_price": round(sum(c["price"] for c in comps) / max(len(comps), 1), 2),
        "avg_rating": round(sum(c["rating"] for c in comps) / max(len(comps), 1), 1),
        "total_market_monthly_sales": sum(c["estimated_monthly_sales"] for c in comps),
        "price_range": {"min": min(c["price"] for c in comps), "max": max(c["price"] for c in comps)},
        "competitors": comps, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def tool_score_opportunity(product_name: str, niche: str = "Home & Kitchen") -> Dict:
    trends = generate_mock_trends(niche)
    products = generate_mock_amazon_products(niche, 5)
    comps = generate_mock_competitors(product_name)
    product = next((p for p in products if product_name.lower() in p["title"].lower()), products[0] if products else {"title": product_name, "price": 39.99, "seller_count": 15, "rating": 4.0, "fba_available": True})
    product["title"] = product_name
    scores = score_product(product, trends, comps)
    return {
        "product": product_name, "niche": niche, **scores,
        "trend_data": {"velocity": trends["trend_velocity"], "direction": trends["trend_direction"], "current_interest": trends["current_interest"]},
        "competition_summary": {"total_sellers": len(comps), "avg_price": round(sum(c["price"] for c in comps) / max(len(comps), 1), 2)},
    }


def tool_generate_report(niche: str = "Home & Kitchen") -> Dict:
    trends = generate_mock_trends(niche)
    products = generate_mock_amazon_products(niche, 10)
    scored = []
    for p in products[:8]:
        comps = generate_mock_competitors(p["title"])
        s = score_product(p, trends, comps)
        scored.append({**p, **s})
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    past = retrieve_research(niche)
    analytics["reports_generated"] += 1
    recs = _build_recommendations(scored[:3], trends, past)
    es = {
        "total_products_analyzed": len(products), "top_opportunities": len([p for p in scored if p["composite_score"] >= 65]),
        "avg_composite_score": round(sum(p["composite_score"] for p in scored) / max(len(scored), 1), 1),
        "trend_direction": trends["trend_direction"], "trend_velocity": trends["trend_velocity"],
    }
    return {
        "report_id": f"RPT-{uuid.uuid4().hex[:8].upper()}", "title": f"Product Research Report: {niche}",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "niche": niche,
        "executive_summary": es, "top_products": scored[:5],
        "trend_data": {"velocity": trends["trend_velocity"], "direction": trends["trend_direction"], "rising_queries": trends["rising_queries"][:5]},
        "historical_context": past[:3], "recommendations": recs,
    }


def _build_recommendations(top: List[Dict], trends: Dict, past: List[Dict]) -> List[str]:
    recs = []
    if top:
        b = top[0]
        recs.append(f"**Top Pick: {b['title']}** — Score {b['composite_score']}/100, est. margin {b['estimated_margin_pct']}%. {'Strong upward trend supports immediate launch.' if trends['trend_velocity'] > 20 else 'Moderate trend — validate with small test order.'}")
    if trends["trend_velocity"] > 30:
        recs.append(f"**Trend Alert**: {trends['niche']} showing {trends['trend_velocity']}% growth. Act within 2-3 weeks for first-mover advantage.")
    elif trends["trend_velocity"] < -10:
        recs.append(f"**Caution**: {trends['niche']} declining ({trends['trend_velocity']}%). Consider adjacent niches.")
    for r in past[:2]:
        if r["outcome"] == "failed":
            recs.append(f"**Historical Warning**: *{r['product_name']}* in {r['niche']} failed — {r['reason']} Avoid similar issues.")
        elif r["outcome"] == "winner":
            recs.append(f"**Proven Pattern**: *{r['product_name']}* was a winner ({r['margin_pct']}% margin, {r['months_active']}mo). Look for similar products.")
    if len(top) >= 2:
        recs.append(f"**Diversify**: Launch both {top[0]['title']} and {top[1]['title']} to spread risk.")
    return recs


def tool_get_sales_summary(months: int = 3) -> Dict:
    if not sales_data:
        return {"error": "No sales data loaded."}
    cutoff = datetime.now() - timedelta(days=months * 30)
    recent = [s for s in sales_data if datetime.strptime(s["date"], "%Y-%m-%d") >= cutoff]
    if not recent:
        recent = sales_data[-500:]
    by_product = defaultdict(lambda: {"revenue": 0, "profit": 0, "quantity": 0, "orders": 0})
    by_category = defaultdict(lambda: {"revenue": 0, "profit": 0, "quantity": 0})
    by_store = defaultdict(lambda: {"revenue": 0, "profit": 0})
    total_rev = total_profit = total_ad = 0
    for s in recent:
        by_product[s["product_name"]]["revenue"] += s["revenue"]
        by_product[s["product_name"]]["profit"] += s["profit"]
        by_product[s["product_name"]]["quantity"] += s["quantity"]
        by_product[s["product_name"]]["orders"] += 1
        by_category[s["category"]]["revenue"] += s["revenue"]
        by_category[s["category"]]["profit"] += s["profit"]
        by_category[s["category"]]["quantity"] += s["quantity"]
        by_store[s["store"]]["revenue"] += s["revenue"]
        by_store[s["store"]]["profit"] += s["profit"]
        total_rev += s["revenue"]; total_profit += s["profit"]; total_ad += s["ad_spend"]
    top_products = sorted([{"name": k, **{kk: round(vv, 2) for kk, vv in v.items()}} for k, v in by_product.items()], key=lambda x: x["revenue"], reverse=True)[:10]
    categories = sorted([{"category": k, **{kk: round(vv, 2) for kk, vv in v.items()}} for k, v in by_category.items()], key=lambda x: x["revenue"], reverse=True)
    stores_list = sorted([{"store": k, **{kk: round(vv, 2) for kk, vv in v.items()}} for k, v in by_store.items()], key=lambda x: x["revenue"], reverse=True)
    return {
        "period": f"Last {months} month(s)", "total_revenue": round(total_rev, 2), "total_profit": round(total_profit, 2),
        "total_ad_spend": round(total_ad, 2), "overall_margin": round(total_profit / total_rev * 100, 1) if total_rev > 0 else 0,
        "roas": round(total_rev / total_ad, 2) if total_ad > 0 else 0, "total_orders": len(recent),
        "top_products": top_products, "categories": categories, "stores": stores_list,
    }


AGENT_TOOLS = {
    "search_trends": {"fn": tool_search_trends, "description": "Search Google Trends for a niche", "trigger_keywords": ["trend", "trending", "google trends", "rising", "popular", "what's hot", "demand", "search volume"]},
    "search_amazon": {"fn": tool_search_amazon, "description": "Search Amazon products", "trigger_keywords": ["amazon", "bsr", "best seller", "product search", "find products", "amazon products"]},
    "analyze_competitors": {"fn": tool_analyze_competitors, "description": "Analyze competitors", "trigger_keywords": ["competitor", "competition", "who sells", "competing", "rival", "competitive"]},
    "score_opportunity": {"fn": tool_score_opportunity, "description": "Score a product opportunity", "trigger_keywords": ["score", "evaluate", "opportunity", "should i sell", "worth it", "potential", "viable"]},
    "generate_report": {"fn": tool_generate_report, "description": "Generate research report", "trigger_keywords": ["report", "research report", "full analysis", "comprehensive", "deep dive", "market report"]},
    "get_sales_summary": {"fn": tool_get_sales_summary, "description": "Analyze sales performance", "trigger_keywords": ["sales", "revenue", "profit", "performance", "how are we doing", "top products"]},
}


def detect_tool_call(query: str) -> Optional[str]:
    ql = query.lower()
    best, best_score = None, 0
    for name, info in AGENT_TOOLS.items():
        score = sum(1 for kw in info["trigger_keywords"] if kw in ql)
        if score > best_score:
            best_score = score; best = name
    return best if best_score > 0 else None


def extract_niche(query: str) -> str:
    ql = query.lower()
    for niche in PRODUCT_NICHES:
        if niche.lower() in ql:
            return niche
    kw_map = {
        "Home & Kitchen": ["home", "kitchen", "cooking", "appliance"],
        "Beauty & Personal Care": ["beauty", "skincare", "cosmetic", "makeup"],
        "Health & Wellness": ["health", "wellness", "supplement", "vitamin"],
        "Pet Supplies": ["pet", "dog", "cat", "animal"],
        "Electronics & Gadgets": ["electronic", "gadget", "tech", "phone"],
        "Fitness & Sports": ["fitness", "sport", "gym", "exercise", "workout"],
        "Baby & Kids": ["baby", "kid", "child", "toddler"],
        "Outdoor & Garden": ["outdoor", "garden", "patio", "camping"],
        "Fashion & Accessories": ["fashion", "clothing", "jewelry", "watch"],
        "Automotive": ["car", "auto", "vehicle"],
        "Office & Productivity": ["office", "desk", "productivity"],
        "Toys & Games": ["toy", "game", "puzzle"],
    }
    for niche, kws in kw_map.items():
        if any(k in ql for k in kws):
            return niche
    return "Home & Kitchen"


CATEGORY_KEYWORDS = {
    "trends": ["trend", "trending", "rising", "popular", "demand"],
    "competition": ["competitor", "competition", "rival", "market"],
    "product_research": ["find products", "product ideas", "what to sell", "winning"],
    "sourcing": ["supplier", "source", "alibaba", "manufacturer"],
    "pricing": ["price", "pricing", "margin", "profit", "cost"],
    "advertising": ["ad", "advertising", "facebook", "ppc", "marketing"],
    "sales_analysis": ["sales", "revenue", "performance", "top products"],
    "report": ["report", "analysis", "comprehensive", "deep dive"],
}


def detect_category(query: str) -> Optional[str]:
    ql = query.lower()
    scores = {cat: sum(1 for kw in kws if kw in ql) for cat, kws in CATEGORY_KEYWORDS.items()}
    scores = {k: v for k, v in scores.items() if v > 0}
    return max(scores, key=scores.get) if scores else None


# ─── Response Generation ─────────────────────────────────────
def generate_response(query: str, chunks: List[Dict], tool_result: Optional[Dict] = None, tool_name: Optional[str] = None, past_ctx: Optional[List[Dict]] = None) -> Dict:
    citations = []
    answer_parts = []
    for i, chunk in enumerate(chunks):
        citations.append({"id": i + 1, "source": chunk.get("title", "Unknown"), "section": chunk.get("section", ""), "page": chunk.get("page"), "relevance": chunk.get("relevance_score", 0), "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]})

    if tool_result and not tool_result.get("error"):
        if tool_name == "search_trends":
            t = tool_result
            answer_parts.append(f"**Google Trends Analysis: {t['niche']}** ({t['period']})\n\n- **Current Interest**: {t['current_interest']}/100\n- **Trend Velocity**: {t['trend_velocity']}% {'📈' if t['trend_velocity'] > 10 else '📉' if t['trend_velocity'] < -10 else '➡️'}\n- **Direction**: {t['trend_direction'].title()}\n\n**Rising Search Queries:**")
            for rq in t.get("rising_queries", [])[:5]:
                emoji = "🔥" if rq["trend"] == "breakout" else "📈"
                answer_parts.append(f"- {emoji} **{rq['query']}** — {rq['search_volume']:,} searches/mo, +{rq['growth_pct']}% growth")

        elif tool_name == "search_amazon":
            a = tool_result
            answer_parts.append(f"**Amazon Product Search: {a['niche']}**\n\nFound **{a['total_products']}** products:\n")
            for i, p in enumerate(a.get("products", [])[:6], 1):
                answer_parts.append(f"**{i}. {p['title']}**\n   💰 ${p['price']:.2f} | ⭐ {p['rating']} ({p['review_count']:,} reviews) | BSR #{p['bsr']:,} | ~{p['estimated_monthly_sales']:,} units/mo | {p['seller_count']} sellers")

        elif tool_name == "analyze_competitors":
            c = tool_result
            answer_parts.append(f"**Competitor Analysis: {c['product']}**\n\n- **Total Competitors**: {c['total_competitors']}\n- **Avg Price**: ${c['avg_price']:.2f} (${c['price_range']['min']:.2f} – ${c['price_range']['max']:.2f})\n- **Avg Rating**: {c['avg_rating']}/5.0\n- **Market Sales**: ~{c['total_market_monthly_sales']:,} units/mo\n\n**Top Competitors:**")
            for comp in c.get("competitors", [])[:5]:
                ad_info = f" | Ad: ~${comp['estimated_ad_spend']:,.0f}/mo" if comp.get("estimated_ad_spend") else ""
                answer_parts.append(f"- **{comp['store_name']}** ({comp['platform']}) — ${comp['price']:.2f} | ⭐ {comp['rating']} ({comp['review_count']:,} reviews) | ~{comp['estimated_monthly_sales']:,} units/mo | {comp['shipping_speed']}{ad_info}")
            low_rated = [comp for comp in c.get("competitors", []) if comp["rating"] < 3.8]
            if low_rated:
                answer_parts.append(f"\n🎯 **Insight**: {len(low_rated)} competitor(s) rated below 3.8 — quality differentiation opportunity")

        elif tool_name == "score_opportunity":
            s = tool_result
            stars = "★" * s["confidence"] + "☆" * (5 - s["confidence"])
            answer_parts.append(f"**Product Opportunity Score: {s['product']}**\n\n- **Composite Score**: {s['composite_score']}/100\n- **Confidence**: {stars}\n- **Est. Margin**: {s['estimated_margin_pct']}%\n- **Est. Landed Cost**: ${s['estimated_landed_cost']:.2f}\n\n**7-Dimension Breakdown:**")
            dim_emojis = {"trend_velocity": "📈", "competition_density": "🏪", "margin_potential": "💰", "shipping_feasibility": "🚚", "review_sentiment_gap": "⭐", "seasonality_risk": "📅", "ad_creative_potential": "🎨"}
            for dn, dd in s.get("dimensions", {}).items():
                bar = "█" * (dd["score"] // 10) + "░" * (10 - dd["score"] // 10)
                answer_parts.append(f"- {dim_emojis.get(dn, '📊')} **{dn.replace('_', ' ').title()}**: {dd['score']}/100 [{bar}] ({dd['weight']})")

        elif tool_name == "generate_report":
            r = tool_result
            es = r["executive_summary"]
            answer_parts.append(f"**📊 Product Research Report: {r['niche']}**\n*Report ID: {r['report_id']} | {r['generated_at']}*\n\n**Executive Summary:**\n- Products Analyzed: {es['total_products_analyzed']}\n- Top Opportunities: {es['top_opportunities']}\n- Avg Score: {es['avg_composite_score']}/100\n- Trend: {es['trend_direction'].title()} ({es['trend_velocity']}%)\n\n**Top 5 Products:**")
            for i, p in enumerate(r.get("top_products", [])[:5], 1):
                stars = "★" * p["confidence"] + "☆" * (5 - p["confidence"])
                answer_parts.append(f"**{i}. {p['title']}** — Score: {p['composite_score']}/100 | {stars} | Margin: {p['estimated_margin_pct']}% | ${p['price']:.2f} | BSR #{p['bsr']:,}")
            if r.get("recommendations"):
                answer_parts.append("\n**Recommendations:**")
                for rec in r["recommendations"]:
                    answer_parts.append(f"- {rec}")

        elif tool_name == "get_sales_summary":
            ss = tool_result
            answer_parts.append(f"**Sales Performance** ({ss['period']})\n\n- **Revenue**: ${ss['total_revenue']:,.2f}\n- **Profit**: ${ss['total_profit']:,.2f}\n- **Margin**: {ss['overall_margin']}%\n- **Ad Spend**: ${ss['total_ad_spend']:,.2f}\n- **ROAS**: {ss['roas']}x\n- **Orders**: {ss['total_orders']:,}\n\n**Top Products:**")
            for i, p in enumerate(ss.get("top_products", [])[:5], 1):
                margin = round(p["profit"] / p["revenue"] * 100, 1) if p["revenue"] > 0 else 0
                answer_parts.append(f"- **{i}. {p['name']}** — ${p['revenue']:,.2f} rev | ${p['profit']:,.2f} profit ({margin}% margin)")

    if chunks:
        if answer_parts:
            answer_parts.append("\n\n---\n\n**Relevant Knowledge:**")
        best = chunks[0]
        answer_parts.append(f"According to **{best.get('title', '')}**, **{best.get('section', '')}**:\n\n> {best['text']}")
        for c in chunks[1:3]:
            answer_parts.append(f"\n- **{c.get('section', '')}** ({c.get('title', '')}): {c['text'][:150]}...")

    if past_ctx:
        answer_parts.append("\n\n**From Your History (RAG):**")
        for r in past_ctx[:2]:
            icon = "✅" if r["outcome"] == "winner" else "❌" if r["outcome"] == "failed" else "➡️"
            answer_parts.append(f"- {icon} **{r['product_name']}** ({r['niche']}) — {r['outcome'].title()}: {r['reason']} (Margin: {r['margin_pct']}%)")

    if not answer_parts:
        answer_parts.append("I'm your E-Commerce Product Research Agent! I can help with:\n\n- **Trend Analysis** — \"What's trending in Home & Kitchen?\"\n- **Amazon Research** — \"Find products on Amazon in Pet Supplies\"\n- **Competitor Analysis** — \"Analyze competitors for portable ice maker\"\n- **Opportunity Scoring** — \"Score the opportunity for LED closet lights\"\n- **Full Reports** — \"Generate a research report for Beauty & Personal Care\"\n- **Sales Analysis** — \"How are our sales performing?\"\n\nUpload your sales CSV for personalized insights powered by RAG!")

    return {"answer": "\n".join(answer_parts), "citations": citations, "tool_used": tool_name, "tool_result": tool_result if tool_result and not tool_result.get("error") else None}


# ─── CSV Parsing ──────────────────────────────────────────────
def parse_sales_csv(content: str, filename: str) -> List[Dict]:
    parsed = []
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames or []
    col_map = {}
    for col in fieldnames:
        cl = col.lower().strip()
        if any(k in cl for k in ["date", "order date"]):
            col_map["date"] = col
        elif any(k in cl for k in ["product", "item", "name", "sku"]):
            col_map["product"] = col
        elif any(k in cl for k in ["revenue", "sales", "total", "amount"]):
            col_map["revenue"] = col
        elif any(k in cl for k in ["cost", "cogs"]):
            col_map["cost"] = col
        elif any(k in cl for k in ["quantity", "qty", "units"]):
            col_map["quantity"] = col
        elif any(k in cl for k in ["category", "niche"]):
            col_map["category"] = col
        elif any(k in cl for k in ["store", "channel", "platform"]):
            col_map["store"] = col
    if "date" not in col_map or "revenue" not in col_map:
        if len(fieldnames) >= 3:
            col_map = {"date": fieldnames[0], "product": fieldnames[1], "revenue": fieldnames[2]}
        else:
            return []
    for row in reader:
        try:
            date_str = row.get(col_map["date"], "").strip()
            product = row.get(col_map.get("product", ""), "Unknown").strip()
            rev_str = row.get(col_map["revenue"], "0").strip().replace("$", "").replace(",", "")
            revenue = float(rev_str)
            cost_str = row.get(col_map.get("cost", ""), "0").strip().replace("$", "").replace(",", "")
            cost = float(cost_str) if cost_str else revenue * 0.3
            qty_str = row.get(col_map.get("quantity", ""), "1").strip()
            qty = int(float(qty_str)) if qty_str else 1
            date_parsed = None
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    date_parsed = datetime.strptime(date_str, fmt); break
                except ValueError:
                    continue
            if not date_parsed:
                continue
            ad_spend = round(revenue * random.uniform(0.10, 0.25), 2)
            fee = round(revenue * random.uniform(0.03, 0.15), 2)
            profit = round(revenue - cost - ad_spend - fee, 2)
            parsed.append({
                "id": str(uuid.uuid4()), "date": date_parsed.strftime("%Y-%m-%d"),
                "product_name": product, "category": row.get(col_map.get("category", ""), "Uncategorized").strip() or "Uncategorized",
                "store": row.get(col_map.get("store", ""), "Uploaded Store").strip() or "Uploaded Store",
                "quantity": qty, "revenue": round(revenue, 2), "cost": round(cost, 2),
                "ad_spend": ad_spend, "platform_fee": fee, "profit": profit,
                "margin_pct": round(profit / revenue * 100, 1) if revenue > 0 else 0, "source": "uploaded",
            })
        except (ValueError, KeyError):
            continue
    return parsed


# ─── Pydantic Models ─────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    message: str
    answer: str
    citations: List[Dict[str, Any]]
    category: Optional[str]
    tool_used: Optional[str]
    tool_result: Optional[Dict[str, Any]]
    processing_time: float
    timestamp: str

class FeedbackRequest(BaseModel):
    session_id: str
    message_index: int
    rating: str
    comment: Optional[str] = None


# ─── Routes ──────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    initialize_knowledge_base()
    sales_data.extend(generate_sample_sales())
    product_research.extend(generate_sample_research())
    print(f"🚀 E-Commerce Product Researcher API starting...")
    print(f"📚 Loaded {len(knowledge_chunks)} knowledge chunks")
    print(f"💰 Pre-loaded {len(sales_data)} sample sales records (12 months)")
    print(f"🔬 Pre-loaded {len(product_research)} past research records")


@app.get("/")
async def root():
    return {
        "name": "E-Commerce Product Researcher Agent API", "version": "1.0.0", "status": "running", "docs": "/docs",
        "endpoints": {
            "chat": "POST /api/v1/chat", "trends": "GET /api/v1/trends/{niche}",
            "amazon": "GET /api/v1/amazon/{niche}", "competitors": "GET /api/v1/competitors/{product}",
            "score": "GET /api/v1/score/{product}", "report": "GET /api/v1/report/{niche}",
            "sales": "GET /api/v1/sales/summary", "upload": "POST /api/v1/sales/upload",
            "research_history": "GET /api/v1/research/history", "analytics": "GET /api/v1/analytics",
            "health": "GET /api/v1/health",
        },
    }


@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "service": "ecommerce-product-researcher", "version": "1.0.0", "knowledge_chunks": len(knowledge_chunks), "sales_records": len(sales_data), "research_records": len(product_research)}


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    category = detect_category(query)
    niche = extract_niche(query)
    tool_name = detect_tool_call(query)
    tool_result = None
    if tool_name:
        tool_fn = AGENT_TOOLS[tool_name]["fn"]
        if tool_name == "search_trends":
            tool_result = tool_fn(niche)
        elif tool_name == "search_amazon":
            tool_result = tool_fn(niche)
        elif tool_name == "analyze_competitors":
            product = query.split("for ")[-1].strip() if "for " in query else query.split("competitor")[-1].strip()
            product = product.strip("?.,! ") or "Portable Ice Maker"
            tool_result = tool_fn(product)
        elif tool_name == "score_opportunity":
            product = query.split("for ")[-1].strip() if "for " in query else query.split("score")[-1].strip()
            product = product.strip("?.,! ") or "Portable Ice Maker"
            tool_result = tool_fn(product, niche)
        elif tool_name == "generate_report":
            tool_result = tool_fn(niche)
        elif tool_name == "get_sales_summary":
            tool_result = tool_fn(3)
        else:
            tool_result = tool_fn()

    chunks = retrieve_chunks(query, top_k=3)
    past_ctx = retrieve_research(query, top_k=2)
    response_data = generate_response(query, chunks, tool_result, tool_name, past_ctx)
    processing_time = round(time.time() - start_time, 3)

    analytics["total_queries"] += 1
    analytics["total_response_time"] += processing_time
    analytics["avg_response_time"] = round(analytics["total_response_time"] / analytics["total_queries"], 3)
    analytics["products_researched"] += 1 if tool_name in ["score_opportunity", "analyze_competitors"] else 0
    if category:
        analytics["queries_by_type"][category] = analytics["queries_by_type"].get(category, 0) + 1

    chat_sessions[session_id].append({"role": "user", "content": query})
    chat_sessions[session_id].append({"role": "assistant", "content": response_data["answer"], "citations": response_data["citations"]})

    return ChatResponse(
        session_id=session_id, message=query, answer=response_data["answer"],
        citations=response_data["citations"], category=category,
        tool_used=response_data.get("tool_used"), tool_result=response_data.get("tool_result"),
        processing_time=processing_time, timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.get("/api/v1/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    return {"session_id": session_id, "messages": chat_sessions.get(session_id, [])}


@app.post("/api/v1/chat/feedback")
async def submit_feedback(request: FeedbackRequest):
    if request.rating == "positive":
        analytics["feedback_positive"] += 1
    else:
        analytics["feedback_negative"] += 1
    return {"success": True, "message": "Feedback recorded."}


@app.get("/api/v1/trends/{niche}")
async def get_trends(niche: str):
    return tool_search_trends(niche)


@app.get("/api/v1/amazon/{niche}")
async def get_amazon_products(niche: str, count: int = 10):
    return tool_search_amazon(niche, count)


@app.get("/api/v1/competitors/{product}")
async def get_competitors(product: str):
    return tool_analyze_competitors(product)


@app.get("/api/v1/score/{product}")
async def get_score(product: str, niche: str = "Home & Kitchen"):
    return tool_score_opportunity(product, niche)


@app.get("/api/v1/report/{niche}")
async def get_report(niche: str):
    return tool_generate_report(niche)


@app.get("/api/v1/sales/summary")
async def get_sales_summary(months: int = 3):
    return tool_get_sales_summary(months)


@app.post("/api/v1/sales/upload")
async def upload_sales(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    parsed = parse_sales_csv(text, file.filename)
    if not parsed:
        raise HTTPException(status_code=400, detail="Could not parse CSV. Ensure it has Date and Revenue columns.")
    sales_data.extend(parsed)
    sales_data.sort(key=lambda x: x["date"])
    file_id = f"sales-{uuid.uuid4().hex[:8]}"
    uploaded_files.append({"id": file_id, "filename": file.filename, "upload_time": time.strftime("%Y-%m-%d %H:%M:%S"), "records_parsed": len(parsed), "size_bytes": len(content)})
    analytics["files_uploaded"] += 1
    total_rev = sum(r["revenue"] for r in parsed)
    total_profit = sum(r["profit"] for r in parsed)
    return {
        "success": True, "file": {"id": file_id, "filename": file.filename, "records_parsed": len(parsed)},
        "quick_summary": {"total_revenue": round(total_rev, 2), "total_profit": round(total_profit, 2), "date_range": f"{parsed[0]['date']} to {parsed[-1]['date']}" if parsed else "N/A"},
        "message": f"Parsed {len(parsed)} sales records from '{file.filename}'.",
    }


@app.get("/api/v1/sales/files")
async def list_uploaded_files():
    return {"total": len(uploaded_files), "files": uploaded_files}


@app.get("/api/v1/research/history")
async def get_research_history():
    return {"total": len(product_research), "records": sorted(product_research, key=lambda x: x["date_researched"], reverse=True)}


@app.get("/api/v1/niches")
async def get_niches():
    return {"niches": PRODUCT_NICHES}


@app.get("/api/v1/analytics")
async def get_analytics():
    total_fb = analytics["feedback_positive"] + analytics["feedback_negative"]
    return {
        **analytics,
        "satisfaction_rate": round(analytics["feedback_positive"] / total_fb * 100, 1) if total_fb > 0 else 0,
        "active_sessions": len(chat_sessions), "knowledge_chunks": len(knowledge_chunks),
        "sales_records": len(sales_data), "research_records": len(product_research),
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
