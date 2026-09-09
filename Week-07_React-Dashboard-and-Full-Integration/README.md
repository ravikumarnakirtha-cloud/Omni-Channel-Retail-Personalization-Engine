#  Week 7 — React Dashboard & Full-Stack Integration

## Week Goal
Run the complete Omni-Channel Retail Personalization Engine end-to-end — all services plus the React analytics dashboard. By end of week your team can browse the Overview charts (revenue trends, segment pie, channel distribution), explore customer segments, get live personalized recommendations for any customer, and trigger personalized offers — all through a browser.

---

## What's Inside

```
Week-07_React-Dashboard-and-Full-Integration/
├── docker-compose.yml               ← FULL STACK — all containers
├── database/schema.sql
├── datasets/                        ← All 5 CSVs + generate_datasets.py
├── configs/.env.example
├── feature-service/                 ← Feature/RFM computation
├── api-gateway/                     ← Node.js gateway (rate-limit + cache)
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json                 ← React 18, Recharts, Axios, Tailwind
    └── src/
        ├── App.jsx                  ← 4-tab dashboard: Overview, Segments, Recommendations, Products
        └── App.css
```

---

## Quick Start — Full Platform

```bash
cd Week-07_React-Dashboard-and-Full-Integration

docker compose up -d --build
```

>  First build: 5–8 minutes (npm install + Python deps)

Monitor startup:
```bash
docker compose ps
docker compose logs -f
```

---

## Open the Dashboard

| URL | What You See |
|-----|-------------|
| **http://localhost:3000** | **React Dashboard (4 tabs)** |
| http://localhost:3001 | API Gateway (route list) |
| http://localhost:8002/docs | Feature Service Swagger |

---

## Dashboard Tabs

### Tab 1: Overview
- **Revenue trend** — bar chart of monthly transaction totals
- **Segment pie chart** — High Value / Frequent Buyer / At Risk / New Customer breakdown
- **Channel distribution** — Web vs In-Store vs Mobile split

### Tab 2: Segments
- **RFM summary table** — avg recency, frequency, monetary per segment
- **Revenue by segment** — bar chart showing which segment drives most revenue
- Identify which segment is "At Risk" and quantify the revenue at stake

### Tab 3: Recommendations
- **Select any customer** from dropdown (populated from live API)
- Click **Get Recommendations** → see top-5 personalized products with:
  - Recommendation score (0–1)
  - Offer type (exclusive_bundle / loyalty_reward / win-back / welcome)
  - Discount percentage
  - Reason (collaborative_filtering / category_affinity / segment_default)
- Click **Trigger Offer** → fires email/SMS/push notification via Notification Service

### Tab 4: Products
- Searchable product catalogue
- Filter by category, brand, price range
- See which products are most recommended across the customer base

---

## Full End-to-End API Test

```bash
# 1. Get a real user ID from the dataset
USER_ID=$(head -2 datasets/users.csv | tail -1 | cut -d',' -f1)

# 2. Health check
curl http://localhost:3001/api/health | python3 -m json.tool

# 3. Get user features
curl "http://localhost:3001/api/segment/$USER_ID" | python3 -m json.tool

# 4. Analytics summary
curl http://localhost:3001/api/analytics/summary | python3 -m json.tool

# 5. Ingest a real-time event
curl -s -X POST http://localhost:3001/api/ingest/event \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"event_type\":\"add_to_cart\",\"channel\":\"mobile\"}" \
  | python3 -m json.tool

# 6. Trigger a personalized offer
curl -s -X POST http://localhost:3001/api/trigger-offer \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"$USER_ID\",\"channel\":\"email\"}" \
  | python3 -m json.tool

# 7. Gateway stats
curl http://localhost:3001/api/gateway/stats | python3 -m json.tool
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Dashboard blank | `docker compose logs retail_frontend` — check nginx started |
| API 502 errors | `docker compose logs retail_feature` — check data loaded |
| Kafka not ready | Wait 60s more — Kafka/Zookeeper are slow to initialize |
| Port conflict | Change host ports in `docker-compose.yml` |

### Full reset
```bash
docker compose down -v
docker compose up -d --build
```

---

## Teardown
```bash
docker compose down        # keep volumes
docker compose down -v     # wipe everything
```

---

## Learning Objectives
- See the complete omni-channel personalization flow: data → features → segments → offers → dashboard
- Understand how React fetches live data from microservices via the API Gateway
- Learn how Recharts renders real retail analytics (revenue trends, segment distribution)
- Understand the full Next-Best-Offer pipeline: segment label → offer type → channel → send
- See rate limiting and caching in action: watch `_cached: true` appear on repeated dashboard loads
- Understand the business value: which segment deserves which offer, and why 25% off for At-Risk
