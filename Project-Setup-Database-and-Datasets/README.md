#  Week 1 — Project Setup, Database & Datasets

##  Week Goal
Boot the core infrastructure — PostgreSQL for retail data and Redis for caching — and apply the full retail schema. Generate or use the pre-built datasets (500 users, 5,000 transactions, 15,000 web events across web/store/mobile channels). By end of week you have a live retail database ready to explore.

---

##  What's Inside

```
Week-01_Project-Setup-Database-and-Datasets/
├── docker-compose.yml           ← PostgreSQL + Redis only
├── database/
│   └── schema.sql               ← Full retail schema (8 tables + indexes)
├── datasets/
│   ├── users.csv                ← 500 customers (age, gender, city, channel preference)
│   ├── products.csv             ← 37 products across 7 categories
│   ├── transactions.csv         ← 5,000 purchases (web/store/mobile)
│   ├── events.csv               ← 15,000 behavioural events (clicks, views, cart adds)
│   ├── social_interactions.csv  ← 250 social signals (likes, shares)
│   └── generate_datasets.py     ← Regenerate all CSVs with fresh UUIDs
└── configs/
    └── .env.example
```

---

##  Quick Start

```bash
cd Week-01_Project-Setup-Database-and-Datasets
docker compose up -d
```

PostgreSQL auto-runs `schema.sql` on first boot (~15s).

---

##  Verify It's Working

### 1. Check containers
```bash
docker compose ps
# retail_postgres: healthy | retail_redis: healthy
```

### 2. List tables
```bash
docker exec -it retail_postgres psql -U retail -d retail_db -c "\dt"
```
Expected: `users`, `products`, `transactions`, `events`, `customer_segments`, `recommendations`, `notifications`

### 3. Count seeded products
```bash
docker exec -it retail_postgres psql -U retail -d retail_db \
  -c "SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY 2 DESC;"
```

### 4. Ping Redis
```bash
docker exec -it retail_redis redis-cli ping
# → PONG
```

### 5. Explore the CSV data (Python)
```bash
pip install pandas
python3 -c "
import pandas as pd
txn = pd.read_csv('datasets/transactions.csv')
print(txn.groupby('channel')['amount'].agg(['count','sum']).round(2))
"
```

### 6. Regenerate datasets with fresh UUIDs
```bash
cd datasets && python3 generate_datasets.py
```

---

##  Database Schema

| Table | Purpose |
|-------|---------|
| `users` | 500 customers with demographics + channel preference |
| `products` | Catalogue: Electronics, Footwear, Apparel, Grocery, Sports, Health, Books |
| `transactions` | Every purchase: channel, quantity, amount, discount |
| `events` | Web/mobile behaviour: view, click, add_to_cart, wishlist, share |
| `customer_segments` | ML-assigned segment labels (filled in Week 4) |
| `recommendations` | Generated offers per user (filled in Week 4–5) |
| `notifications` | Email/SMS/Push log (filled in Week 5) |

---

##  Dataset Stats

| Dataset | Rows | Key Fields |
|---------|------|-----------|
| users | 500 | age, gender, location, channel_preference (web/store/mobile) |
| products | 37 | name, category, price, brand |
| transactions | 5,000 | user_id, product_id, channel, amount, discount |
| events | 15,000 | event_type, channel, product_id, session_id |
| social_interactions | 250 | platform, interaction_type |

---

##  Teardown
```bash
docker compose down        # keep data
docker compose down -v     # wipe volumes
```
---

##  Learning Objectives
- Understand omni-channel retail data: what web, store, and mobile events look like
- Learn the RFM data model: transactions feed Recency, Frequency, Monetary signals
- Understand why we store events separately from transactions (behaviour vs purchase intent)
- Read `schema.sql` — note the `customer_segments` and `recommendations` tables that ML will fill
- Explore `generate_datasets.py` to see how realistic retail data is synthetically created
