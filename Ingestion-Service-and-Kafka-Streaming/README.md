#  Week 3 — Ingestion Service & Kafka Event Streaming

## Week Goal
Build and run the Ingestion Service — a FastAPI microservice that accepts real-time omni-channel events (web clicks, in-store scans, mobile interactions) and transactions, and publishes them to Kafka topics. This simulates the live event pipeline that feeds the personalization engine in production. By end of week you will stream real-time events and see them published to Kafka.

---

## What's Inside

```
Week-03_Ingestion-Service-and-Kafka-Streaming/
├── docker-compose.yml                  ← PostgreSQL + Kafka + Zookeeper + Feature + Ingestion
├── database/schema.sql
├── datasets/
├── configs/.env.example
├── feature-service/
└── ingestion-service/
    ├── Dockerfile
    ├── requirements.txt                ← FastAPI, kafka-python
    └── ingestion_app.py                ← Event/transaction ingest + Kafka publish
```

---

## Quick Start

```bash
cd Week-03_Ingestion-Service-and-Kafka-Streaming
docker compose up -d --build
```

Wait ~60 seconds for Kafka to fully initialize. Verify:
```bash
docker compose logs retail_kafka --tail=10
docker compose logs retail_ingestion --tail=10
# Look for: Kafka topic list available
```

---

## Testing the Ingestion Service (Port 8001)

### 1. Health check
```bash
curl http://localhost:8001/ | python3 -m json.tool
# → { "kafka_connected": true/false, "events_logged": 0 }
```

### 2. Ingest a web click event
```bash
USER_ID=$(head -2 datasets/users.csv | tail -1 | cut -d',' -f1)
PRODUCT_ID=$(head -2 datasets/products.csv | tail -1 | cut -d',' -f1)

curl -s -X POST http://localhost:8001/ingest/event \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"event_type\": \"add_to_cart\",
    \"product_id\": \"$PRODUCT_ID\",
    \"channel\": \"web\",
    \"session_id\": \"sess_001\"
  }" | python3 -m json.tool
```

### 3. Ingest an in-store transaction
```bash
curl -s -X POST http://localhost:8001/ingest/transaction \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"product_id\": \"$PRODUCT_ID\",
    \"channel\": \"store\",
    \"quantity\": 2,
    \"amount\": 149.98,
    \"discount\": 10.00
  }" | python3 -m json.tool
```

### 4. Simulate a burst of 50 random events
```bash
curl -s -X POST "http://localhost:8001/simulate/stream?n=50" | python3 -m json.tool
```

### 5. View recent events in the log
```bash
curl http://localhost:8001/events/recent?limit=10 | python3 -m json.tool
```

### 6. Check Kafka topics (if Kafka is running)
```bash
docker exec retail_kafka kafka-topics \
  --bootstrap-server localhost:9092 --list
# → retail-events, retail-transactions, retail-recommendations, retail-notifications
```

### 7. Consume events from Kafka (live stream)
```bash
docker exec retail_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic retail-events \
  --from-beginning --max-messages 5
```

---

## Event Types Supported

| Channel | Event Types |
|---------|------------|
| web | view, click, add_to_cart, wishlist, share |
| store | scan, purchase, return |
| mobile | view, click, add_to_cart, like |
| social | like, share, comment |

---

## Kafka Topics

| Topic | Partitions | Purpose |
|-------|-----------|---------|
| `retail-events` | 4 | All behaviour events |
| `retail-transactions` | 4 | Purchase completions |
| `retail-recommendations` | 2 | Generated offers (written by ML engine) |
| `retail-notifications` | 2 | Notification dispatch triggers |

---

## Swagger UI
Open: **http://localhost:8001/docs**

---

## Teardown
```bash
docker compose down -v
```

---

## Learning Objectives
- Understand the event streaming pattern: why Kafka vs HTTP for high-volume events
- Learn Kafka producer pattern: publish-and-forget for scalable event ingestion
- Understand the difference between an event (behaviour) and a transaction (purchase)
- Learn how omni-channel events (web + store + mobile) are unified into one stream
- Read `ingestion_app.py` — focus on `ingest_event()`, `publish()`, and `simulate_stream()`
