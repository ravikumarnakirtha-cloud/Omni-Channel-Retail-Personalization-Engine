# Week 6 — API Gateway & Full Backend Integration

## Week Goal
Add the Node.js/Express API Gateway as the single unified entry point for all client requests. The gateway handles rate limiting (100 req/min), in-memory response caching (30s TTL), request logging, and proxies to the correct downstream microservice. By end of week the entire backend is wired together through one port — test recommendations, ingestion, segmentation, and notifications all via `localhost:3001`.

---

## What's Inside

```
Week-06_API-Gateway-Integration/
├── docker-compose.yml              ← PostgreSQL + Redis + Feature + API Gateway
├── database/schema.sql
├── datasets/
├── configs/.env.example
├── feature-service/
└── api-gateway/
    ├── Dockerfile
    ├── package.json                ← Express, Axios, express-rate-limit, Morgan
    └── server.js                   ← All gateway routes + caching + rate limiting
```

---

## Quick Start

```bash
cd Week-06_API-Gateway-Integration
docker compose up -d --build
```

Verify:
```bash
docker compose logs retail_gateway --tail=10
# Look for: " API Gateway running on http://localhost:3001"
```

---

## Testing the API Gateway (Port 3001)

### 1. Root — list all routes
```bash
curl http://localhost:3001/ | python3 -m json.tool
```

### 2. Health check — all downstream services
```bash
curl http://localhost:3001/api/health | python3 -m json.tool
# → { "gateway": "healthy", "services": { "feature": "healthy", ... } }
```

### 3. Get RFM features via gateway (cached after first call)
```bash
USER_ID=$(head -2 datasets/users.csv | tail -1 | cut -d',' -f1)

# First call — hits feature-service directly
time curl -s "http://localhost:3001/api/segment/$USER_ID" > /dev/null

# Second call within 30s — served from gateway cache (faster)
time curl -s "http://localhost:3001/api/segment/$USER_ID" | python3 -m json.tool
# Look for: "_cached": true
```

### 4. Analytics summary via gateway
```bash
curl http://localhost:3001/api/analytics/summary | python3 -m json.tool
```

### 5. Get products catalogue
```bash
curl http://localhost:3001/api/products | python3 -m json.tool
```

### 6. Get user list
```bash
curl "http://localhost:3001/api/users?limit=5" | python3 -m json.tool
```

### 7. Ingest an event through gateway
```bash
curl -s -X POST http://localhost:3001/api/ingest/event \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"event_type\": \"click\",
    \"channel\": \"web\"
  }" | python3 -m json.tool
```

### 8. Gateway stats (cache size, request log)
```bash
curl http://localhost:3001/api/gateway/stats | python3 -m json.tool
```

### 9. Test rate limiting (101 requests trigger 429)
```bash
for i in $(seq 1 102); do
  curl -s http://localhost:3001/api/health > /dev/null
done
curl http://localhost:3001/api/health
# → { "error": "Too many requests, please slow down." }
```

---

##  Gateway Route Map

| Method | Path | Proxied To |
|--------|------|-----------|
| GET | `/api/health` | All services health check |
| GET | `/api/segment/:userId` | feature-service `/features/:id` |
| GET | `/api/analytics/summary` | feature-service `/rfm/distribution` |
| GET | `/api/analytics/segments` | feature-service `/channel/usage` |
| GET | `/api/products` | feature-service `/category/affinity` |
| GET | `/api/users` | feature-service `/features/batch` |
| POST | `/api/ingest/event` | ingestion-service `/ingest/event` |
| POST | `/api/ingest/transaction` | ingestion-service `/ingest/transaction` |
| POST | `/api/notify` | notification-service `/send` |
| GET | `/api/gateway/stats` | Gateway internal (no proxy) |

---

## Gateway Features

| Feature | Implementation |
|---------|---------------|
| Rate Limiting | 100 requests/minute per IP (express-rate-limit) |
| Response Caching | 30-second in-memory TTL (Map-based) |
| Request Logging | Morgan combined format + internal ring buffer (500 entries) |
| Timeout | 10 seconds per downstream call |
| Error Handling | 502 with descriptive error on service failure |

---

## Gateway Swagger / Route List
```bash
curl http://localhost:3001/ | python3 -m json.tool
```

---

## Teardown
```bash
docker compose down -v
```

---

## Learning Objectives
- Understand the API Gateway pattern: one entry point, fan-out to microservices
- Learn response caching at the edge: why caching analytics/product data reduces load
- Understand rate limiting: why it protects downstream services from abuse
- Learn the proxy pattern with timeout and error fallback
- See how `_cached: true` signals a cached response to the client
- Read `server.js` — focus on `cacheGet/cacheSet`, the `proxy()` helper, and route handlers
