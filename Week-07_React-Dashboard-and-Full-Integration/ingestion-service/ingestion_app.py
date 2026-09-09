"""
Ingestion Service — Week 3
Accepts real-time events and transactions, validates them,
and simulates publishing to Kafka topics.
"""
import os, json, uuid, random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Retail Ingestion Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory event log (simulates Kafka)
EVENT_LOG = []
KAFKA_AVAILABLE = False

try:
    from kafka import KafkaProducer
    producer = KafkaProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    KAFKA_AVAILABLE = True
    print("✅ Kafka connected")
except Exception:
    print("⚠️  Kafka not available — events stored in memory")

TOPICS = {
    "events": "retail-events",
    "transactions": "retail-transactions",
}

class Event(BaseModel):
    user_id: str
    event_type: str  # click, view, add_to_cart, like, share
    product_id: Optional[str] = None
    channel: str = "web"  # web, store, mobile
    session_id: Optional[str] = None
    metadata: Optional[dict] = {}

class Transaction(BaseModel):
    user_id: str
    product_id: str
    channel: str = "web"
    quantity: int = 1
    amount: float
    discount: float = 0.0

def publish(topic: str, message: dict):
    message["event_id"] = str(uuid.uuid4())
    message["timestamp"] = datetime.utcnow().isoformat()
    EVENT_LOG.append({"topic": topic, **message})
    if len(EVENT_LOG) > 1000:
        EVENT_LOG.pop(0)
    if KAFKA_AVAILABLE:
        producer.send(topic, message)
        producer.flush()
    return message

@app.get("/")
def root():
    return {"service": "Ingestion Service", "kafka_connected": KAFKA_AVAILABLE,
            "events_logged": len(EVENT_LOG)}

@app.post("/ingest/event")
def ingest_event(evt: Event):
    msg = publish(TOPICS["events"], evt.dict())
    return {"status": "published", "topic": TOPICS["events"], "event_id": msg["event_id"]}

@app.post("/ingest/transaction")
def ingest_transaction(txn: Transaction):
    msg = publish(TOPICS["transactions"], txn.dict())
    return {"status": "published", "topic": TOPICS["transactions"], "event_id": msg["event_id"]}

@app.get("/events/recent")
def recent_events(limit: int = 20):
    return {"events": EVENT_LOG[-limit:], "total": len(EVENT_LOG)}

@app.post("/simulate/stream")
def simulate_stream(n: int = 20):
    """Simulate n random retail events."""
    channels = ["web", "store", "mobile"]
    event_types = ["view", "click", "add_to_cart", "wishlist", "share"]
    results = []
    for _ in range(n):
        evt = {
            "user_id": str(uuid.uuid4()),
            "event_type": random.choice(event_types),
            "product_id": str(uuid.uuid4()),
            "channel": random.choice(channels),
        }
        results.append(publish(TOPICS["events"], evt))
    return {"simulated": n, "events": results[:5], "total_logged": len(EVENT_LOG)}

if __name__ == "__main__":
    uvicorn.run("ingestion_app:app", host="0.0.0.0", port=8001, reload=True)
