# Week 5 — Notification Service & Next-Best-Offer Engine

## Week Goal
Build and run the Notification & Offer Engine — a FastAPI microservice that translates customer segments into personalized "next-best-offers" (the right offer for the right person at the right time) and simulates sending them across Email, SMS, and Push channels. By end of week you will trigger personalized offers for individual customers and run bulk campaigns for entire segments.

---

## What's Inside

```
Week-05_Notification-Service-and-Offer-Engine/
├── docker-compose.yml                    ← PostgreSQL + Redis + Feature + Notification Services
├── database/schema.sql
├── datasets/
├── configs/.env.example
├── feature-service/
└── notification-service/
    ├── Dockerfile
    ├── requirements.txt
    └── notification_app.py               ← Offer logic + multi-channel notification dispatch
```

---

## Quick Start

```bash
cd Week-05_Notification-Service-and-Offer-Engine
docker compose up -d --build
```

Verify:
```bash
curl http://localhost:8003/ | python3 -m json.tool
```

---

## Testing the Notification Service (Port 8003)

### 1. Root — service status
```bash
curl http://localhost:8003/ | python3 -m json.tool
```

### 2. Send a personalized offer — High Value customer via Email
```bash
USER_ID=$(head -2 datasets/users.csv | tail -1 | cut -d',' -f1)

curl -s -X POST http://localhost:8003/send \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"segment\": \"high_value\",
    \"channel\": \"email\",
    \"product_name\": \"Smart Watch Series 5\"
  }" | python3 -m json.tool
```
Expected:
```json
{
  "status": "sent",
  "offer_type": "exclusive_bundle",
  "discount_pct": 10,
  "channel": "email"
}
```

### 3. Win-back offer — At Risk customer via SMS
```bash
curl -s -X POST http://localhost:8003/send \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"segment\": \"at_risk\",
    \"channel\": \"sms\"
  }" | python3 -m json.tool
# → 25% discount win-back offer
```

### 4. Welcome offer — New customer via Push
```bash
curl -s -X POST http://localhost:8003/send \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"segment\": \"new_customer\",
    \"channel\": \"push\"
  }" | python3 -m json.tool
```

### 5. Bulk campaign — send to 5 users at once
```bash
curl -s -X POST http://localhost:8003/bulk-send \
  -H "Content-Type: application/json" \
  -d '{
    "users": [
      {"user_id": "u001", "segment": "at_risk"},
      {"user_id": "u002", "segment": "frequent_buyer"},
      {"user_id": "u003", "segment": "high_value"}
    ],
    "channel": "email"
  }' | python3 -m json.tool
```

### 6. View all offers by segment
```bash
curl http://localhost:8003/offers/by-segment | python3 -m json.tool
```

### 7. Channel analytics breakdown
```bash
curl http://localhost:8003/analytics/channel-breakdown | python3 -m json.tool
```

### 8. Recent notifications log
```bash
curl "http://localhost:8003/notifications/recent?limit=5" | python3 -m json.tool
```

---

## Next-Best-Offer Logic

| Segment | Offer Type | Discount | Channel Priority |
|---------|-----------|----------|-----------------|
| **High Value** | Exclusive Bundle | 10% | Email → Push |
| **Frequent Buyer** | Loyalty Reward | 15% | Email → SMS |
| **At Risk** | Win-Back Discount | 25% | SMS → Email (urgency) |
| **New Customer** | Welcome Offer | 20% | Email → Push |

---

## Swagger UI
Open: **http://localhost:8003/docs**

---

## Teardown
```bash
docker compose down -v
```

---

## Learning Objectives
- Understand the "Next-Best-Offer" concept: the right offer for the right segment at the right time
- Learn multi-channel notification strategy (email vs SMS vs push — when to use each)
- Understand bulk campaign logic vs individual triggered offers
- See how segment labels (from Week 4) translate directly into offer parameters
- Learn about offer expiry: why time-limited offers drive urgency and conversion
- Read `notification_app.py` — focus on `SEGMENT_OFFERS`, `send_notification()`, and `bulk_send()`
