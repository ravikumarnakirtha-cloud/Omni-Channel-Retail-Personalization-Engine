# Week 4 — Customer Segmentation & ML Engine (K-Means + RFM)

## Week Goal
Build and run the Segmentation Service — a Python FastAPI microservice that trains a K-Means clustering model on RFM features to segment all 500 customers into 4 actionable groups: High Value, Frequent Buyer, At Risk, and New Customer. By end of week you can look up any customer's segment, get the full segment distribution, and identify which customers are at risk of churning.

---

## What's Inside

```
Week-04_Customer-Segmentation-and-ML-Engine/
├── docker-compose.yml              ← PostgreSQL + Redis + Feature + Segmentation Services
├── database/schema.sql
├── datasets/
├── models/                         ← kmeans.pkl auto-generated here on first run
├── configs/.env.example
├── feature-service/
└── segmentation-service/
    ├── Dockerfile
    ├── requirements.txt            ← FastAPI, scikit-learn, Pandas, NumPy
    └── segmentation_app.py         ← K-Means training + segment query endpoints
```

---

## Quick Start

```bash
cd Week-04_Customer-Segmentation-and-ML-Engine
docker compose up -d --build
```

Wait ~30 seconds for model training. Verify:
```bash
docker compose logs retail_segmentation --tail=20
# Look for: " Segmented N users: {'high_value': ..., 'frequent_buyer': ...}"
```

---

## Testing the Segmentation Service (Port 8004)

### 1. Root — segment counts
```bash
curl http://localhost:8004/ | python3 -m json.tool
```

### 2. Get segment for a specific user
```bash
USER_ID=$(head -2 datasets/users.csv | tail -1 | cut -d',' -f1)
curl "http://localhost:8004/segment/$USER_ID" | python3 -m json.tool
```
Expected:
```json
{
  "user_id": "...",
  "segment": "high_value",
  "recency_days": 12,
  "frequency": 18,
  "monetary": 2340.50
}
```

### 3. Full segment summary (business KPIs)
```bash
curl http://localhost:8004/segments/summary | python3 -m json.tool
```
Shows avg recency, frequency, monetary, and total revenue per segment.

### 4. Segment distribution
```bash
curl http://localhost:8004/segments/distribution | python3 -m json.tool
# → e.g. {"high_value": 112, "frequent_buyer": 145, "at_risk": 98, "new_customer": 145}
```

### 5. Top high-value customers (for VIP targeting)
```bash
curl "http://localhost:8004/rfm/top-users?segment=high_value&limit=5" | python3 -m json.tool
```

### 6. Find at-risk customers (churn prevention targets)
```bash
curl "http://localhost:8004/rfm/top-users?segment=at_risk&limit=10" | python3 -m json.tool
```

---

## K-Means Segmentation Model

```
RFM Features (per user)
  └── recency (days since last purchase)
  └── frequency (# purchases)
  └── monetary (total spend)
        ↓
StandardScaler (normalize)
        ↓
K-Means (k=4 clusters, random_state=42)
        ↓
Label clusters by avg monetary (descending):
  Cluster with highest avg spend → "high_value"
  Second highest → "frequent_buyer"
  Third highest → "at_risk"
  Lowest → "new_customer"
        ↓
Model persisted to /models/kmeans.pkl
```

---

## Segment Profiles & Business Actions

| Segment | Recency | Frequency | Monetary | Business Action |
|---------|---------|-----------|----------|----------------|
| **High Value** | Low | High | High | Exclusive bundles, VIP access, 10% off |
| **Frequent Buyer** | Low | Very High | Medium | Loyalty rewards, 15% off |
| **At Risk** | High | Low | Medium | Win-back campaign, 25% off |
| **New Customer** | Medium | Low | Low | Welcome offer, 20% off, onboarding |

---

## Swagger UI
- Feature Service: **http://localhost:8002/docs**
- Segmentation: **http://localhost:8004/docs**

---

## Teardown
```bash
docker compose down -v
```

---

## Learning Objectives
- Understand K-Means clustering applied to customer segmentation
- Learn why StandardScaler is critical before K-Means (RFM features have very different scales)
- Understand the business meaning of each segment and how it maps to marketing actions
- Learn how cluster IDs are mapped to human-readable labels using domain logic
- Understand why `k=4` was chosen — and how to tune it with elbow/silhouette methods
- Read `segmentation_app.py` — focus on `build_rfm()`, `train_kmeans()`, and `label_map`
