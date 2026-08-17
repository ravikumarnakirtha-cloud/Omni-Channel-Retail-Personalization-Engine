#  Week 2 — Feature Engineering Service (RFM + Channel + Category Affinity)

##  Week Goal
Build and run the Feature Engineering Service — a FastAPI microservice that ingests raw transaction and event CSV data and computes the RFM features (Recency, Frequency, Monetary) plus channel usage and category affinity for every customer. These features become the input for the ML segmentation model in Week 4. By end of week you can query any user's full feature profile via API.

---

##  What's Inside

```
Week-02_Feature-Engineering-Service/
├── docker-compose.yml              ← PostgreSQL + Feature Service
├── database/schema.sql
├── datasets/                       ← users.csv, transactions.csv, events.csv, products.csv
├── configs/.env.example
└── feature-service/
    ├── Dockerfile
    ├── requirements.txt            ← FastAPI, Pandas, NumPy, scikit-learn
    └── feature_app.py              ← RFM computation + feature endpoints
```

---

##  Quick Start

```bash
cd Week-02_Feature-Engineering-Service
docker compose up -d --build
```

Verify startup:
```bash
docker compose logs retail_feature --tail=20
# Look for: " Features built for N users"
```

---

##  Testing the Feature API (Port 8002)

### 1. Root — how many users have features
```bash
curl http://localhost:8002/ | python3 -m json.tool
```

### 2. Get features for a specific user
```bash
# First, get a user_id from the dataset
USER_ID=$(head -2 datasets/users.csv | tail -1 | cut -d',' -f1)
curl "http://localhost:8002/features/$USER_ID" | python3 -m json.tool
```
Returns: recency (days since last purchase), frequency (# purchases), monetary (total spend), channel breakdown, category affinity.

### 3. Batch features (first 100 users)
```bash
curl "http://localhost:8002/features/batch?limit=10" | python3 -m json.tool
```

### 4. RFM score distribution (population-level analytics)
```bash
curl http://localhost:8002/rfm/distribution | python3 -m json.tool
```
Returns: mean/median/min/max for recency, frequency, monetary across all users.

### 5. Channel usage breakdown
```bash
curl http://localhost:8002/channel/usage | python3 -m json.tool
# → { "channel_usage": {"web": 1823, "store": 1642, "mobile": 1535}, "total_transactions": 5000 }
```

### 6. Category affinity (top revenue categories)
```bash
curl http://localhost:8002/category/affinity | python3 -m json.tool
```

---

##  RFM Feature Definitions

| Feature | Formula | Meaning |
|---------|---------|---------|
| **Recency** | Days since last transaction | Lower = more engaged |
| **Frequency** | Count of transactions | Higher = more loyal |
| **Monetary** | Sum of all spend | Higher = more valuable |
| **channel_web** | % of transactions via web | Channel mix |
| **channel_store** | % of transactions in-store | Channel mix |
| **channel_mobile** | % of transactions via mobile | Channel mix |
| **cat_Electronics** | # purchases in Electronics | Category affinity |

---

## Swagger UI
Open: **http://localhost:8002/docs**

---

##  Teardown
```bash
docker compose down -v
```

---

##  Learning Objectives
- Understand RFM (Recency-Frequency-Monetary) — the foundation of every retail customer model
- Learn how raw transactions are aggregated into per-user feature vectors using Pandas groupby
- Understand why channel mix matters: a mobile-first customer needs different offers than an in-store customer
- Understand category affinity: past purchases predict future category interest
- Read `feature_app.py` — focus on `build_user_features()` and `startup()`
