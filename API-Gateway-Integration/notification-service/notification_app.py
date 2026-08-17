"""
Notification & Offer Engine — Week 5
Generates personalized next-best-offers by segment and
simulates sending Email / SMS / Push notifications.
"""
import os, uuid, random
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="Notification & Offer Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Notification log (in-memory)
NOTIF_LOG: List[dict] = []

# Offer logic: segment → offer template
SEGMENT_OFFERS = {
    "high_value":      {"offer_type": "exclusive_bundle",    "discount_pct": 10, "message": "Exclusive VIP Bundle — 10% off your next order!"},
    "frequent_buyer":  {"offer_type": "loyalty_reward",     "discount_pct": 15, "message": "You've earned a Loyalty Reward — 15% off!"},
    "at_risk":         {"offer_type": "win_back_discount",  "discount_pct": 25, "message": "We miss you! Come back with 25% off."},
    "new_customer":    {"offer_type": "welcome_offer",      "discount_pct": 20, "message": "Welcome! Enjoy 20% off your next purchase."},
}

CHANNEL_TEMPLATES = {
    "email": {"subject": "🎁 Your Personalized Offer from RetailCo", "format": "html"},
    "sms":   {"subject": None, "format": "plain"},
    "push":  {"subject": "New Offer for You!", "format": "plain"},
}

class NotifyRequest(BaseModel):
    user_id: str
    segment: str = "new_customer"
    channel: str = "email"  # email, sms, push
    product_name: Optional[str] = "Top Pick for You"
    custom_message: Optional[str] = None

class BulkNotifyRequest(BaseModel):
    users: List[dict]  # [{"user_id": ..., "segment": ...}]
    channel: str = "email"

@app.get("/")
def root():
    return {"service": "Notification & Offer Service",
            "notifications_sent": len(NOTIF_LOG),
            "segments_supported": list(SEGMENT_OFFERS.keys())}

@app.post("/send")
def send_notification(req: NotifyRequest):
    """Send a personalized offer notification to a user."""
    offer = SEGMENT_OFFERS.get(req.segment, SEGMENT_OFFERS["new_customer"])
    tmpl  = CHANNEL_TEMPLATES.get(req.channel, CHANNEL_TEMPLATES["email"])

    body = req.custom_message or (
        f"{offer['message']} | Product: {req.product_name} | "
        f"Use code SAVE{offer['discount_pct']} for {offer['discount_pct']}% off."
    )

    notif = {
        "notif_id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "segment": req.segment,
        "channel": req.channel,
        "offer_type": offer["offer_type"],
        "discount_pct": offer["discount_pct"],
        "subject": tmpl["subject"],
        "body": body,
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    }
    NOTIF_LOG.append(notif)
    if len(NOTIF_LOG) > 5000:
        NOTIF_LOG.pop(0)

    return {"status": "sent", "notif_id": notif["notif_id"],
            "channel": req.channel, "offer_type": offer["offer_type"],
            "discount_pct": offer["discount_pct"]}

@app.post("/bulk-send")
def bulk_send(req: BulkNotifyRequest):
    """Send notifications to multiple users."""
    results = []
    for u in req.users:
        offer = SEGMENT_OFFERS.get(u.get("segment", "new_customer"), SEGMENT_OFFERS["new_customer"])
        n = {
            "notif_id": str(uuid.uuid4()),
            "user_id": u["user_id"],
            "segment": u.get("segment", "new_customer"),
            "channel": req.channel,
            "offer_type": offer["offer_type"],
            "discount_pct": offer["discount_pct"],
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
        }
        NOTIF_LOG.append(n)
        results.append({"user_id": u["user_id"], "notif_id": n["notif_id"], "status": "sent"})
    return {"total_sent": len(results), "results": results[:10]}

@app.get("/notifications/recent")
def recent_notifications(limit: int = 20):
    return {"notifications": NOTIF_LOG[-limit:], "total": len(NOTIF_LOG)}

@app.get("/offers/by-segment")
def offers_by_segment():
    return {"segment_offers": SEGMENT_OFFERS}

@app.get("/analytics/channel-breakdown")
def channel_breakdown():
    from collections import Counter
    ch = Counter(n["channel"] for n in NOTIF_LOG)
    seg = Counter(n["segment"] for n in NOTIF_LOG)
    return {"by_channel": dict(ch), "by_segment": dict(seg), "total": len(NOTIF_LOG)}

if __name__ == "__main__":
    uvicorn.run("notification_app:app", host="0.0.0.0", port=8003, reload=True)
