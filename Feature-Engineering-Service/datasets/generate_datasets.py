#!/usr/bin/env python3
"""
Generate realistic mock datasets for the Retail Personalization Engine.
Run: python generate_datasets.py
"""
import csv
import json
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

USERS = 500
PRODUCTS = 50
TRANSACTIONS = 5000
EVENTS = 15000

categories = {
    "Electronics": ["Headphones","Smartwatch","Keyboard","Mouse","Charger","Tablet","Speaker"],
    "Footwear":    ["Running Shoes","Sneakers","Boots","Sandals","Loafers"],
    "Apparel":     ["T-Shirt","Jeans","Jacket","Dress","Hoodie"],
    "Grocery":     ["Green Tea","Coffee","Protein Bar","Nuts","Juice"],
    "Sports":      ["Yoga Mat","Dumbbell","Resistance Band","Water Bottle","Gym Bag"],
    "Health":      ["Vitamin C","Vitamin D","Omega-3","Probiotics","Melatonin"],
    "Books":       ["Python Book","Data Science","Marketing","Finance","Self-Help"],
}
brands = ["TechPro","SpeedRun","TeaLeaf","ZenFit","VitaPlus","DenimCo","HydroLife","AcmeCorp","NovaBrand","PeakGear"]
channels = ["web","store","mobile"]
event_types = ["view","click","add_to_cart","wishlist","share","like"]
genders = ["M","F","Other"]
cities = ["Hyderabad","Mumbai","Delhi","Bangalore","Chennai","Pune","Kolkata","Ahmedabad"]

# ---- Products ----
products = []
product_ids = []
for cat, items in categories.items():
    for item in items:
        pid = str(uuid.uuid4())
        product_ids.append(pid)
        products.append({
            "product_id": pid,
            "name": item,
            "category": cat,
            "price": round(random.uniform(9.99, 499.99), 2),
            "brand": random.choice(brands),
        })

with open("products.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["product_id","name","category","price","brand"])
    w.writeheader(); w.writerows(products)

# ---- Users ----
users = []
user_ids = []
for _ in range(USERS):
    uid = str(uuid.uuid4())
    user_ids.append(uid)
    reg = datetime.now() - timedelta(days=random.randint(30, 730))
    users.append({
        "user_id": uid,
        "name": f"User_{_}",
        "email": f"user{_}@example.com",
        "phone": f"+91{random.randint(7000000000,9999999999)}",
        "age": random.randint(18, 65),
        "gender": random.choice(genders),
        "location": random.choice(cities),
        "registration_date": reg.isoformat(),
        "channel_preference": random.choice(channels),
    })

with open("users.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["user_id","name","email","phone","age","gender","location","registration_date","channel_preference"])
    w.writeheader(); w.writerows(users)

# ---- Transactions ----
transactions = []
for _ in range(TRANSACTIONS):
    uid = random.choice(user_ids)
    pid = random.choice(product_ids)
    product = next(p for p in products if p["product_id"] == pid)
    qty = random.randint(1, 5)
    txn_date = datetime.now() - timedelta(days=random.randint(0, 365))
    transactions.append({
        "transaction_id": str(uuid.uuid4()),
        "user_id": uid,
        "product_id": pid,
        "channel": random.choice(channels),
        "quantity": qty,
        "amount": round(product["price"] * qty, 2),
        "discount": round(random.uniform(0, 20), 2),
        "transaction_date": txn_date.isoformat(),
    })

with open("transactions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["transaction_id","user_id","product_id","channel","quantity","amount","discount","transaction_date"])
    w.writeheader(); w.writerows(transactions)

# ---- Web Events ----
events = []
for _ in range(EVENTS):
    uid = random.choice(user_ids)
    pid = random.choice(product_ids)
    evt_date = datetime.now() - timedelta(days=random.randint(0, 90))
    events.append({
        "event_id": str(uuid.uuid4()),
        "user_id": uid,
        "event_type": random.choice(event_types),
        "product_id": pid,
        "channel": random.choice(channels),
        "session_id": str(uuid.uuid4())[:8],
        "event_timestamp": evt_date.isoformat(),
    })

with open("events.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["event_id","user_id","event_type","product_id","channel","session_id","event_timestamp"])
    w.writeheader(); w.writerows(events)

# ---- Social media interactions ----
social = []
interests = ["tech","fitness","fashion","cooking","travel","music","gaming","wellness"]
for uid in random.sample(user_ids, USERS//2):
    social.append({
        "user_id": uid,
        "liked_categories": ",".join(random.sample(list(categories.keys()), k=random.randint(1,4))),
        "interests": ",".join(random.sample(interests, k=random.randint(1,4))),
        "followers": random.randint(50, 10000),
        "platform": random.choice(["instagram","twitter","facebook"]),
    })

with open("social_interactions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["user_id","liked_categories","interests","followers","platform"])
    w.writeheader(); w.writerows(social)

print(f"✅ Generated:")
print(f"   {len(products)} products → products.csv")
print(f"   {len(users)} users → users.csv")
print(f"   {len(transactions)} transactions → transactions.csv")
print(f"   {len(events)} events → events.csv")
print(f"   {len(social)} social records → social_interactions.csv")
