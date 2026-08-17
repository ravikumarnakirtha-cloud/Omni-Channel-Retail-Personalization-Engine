"""
Feature Engineering Service
Computes RFM features, user profiles, and enriched attributes
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "recommendation-engine"))
from ml_engine import load_data, build_user_features

app = FastAPI(title="Feature Engineering Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

STATE = {}

@app.on_event("startup")
async def startup():
    print("🔄 Feature service loading data...")
    txn, evt, users, products = load_data()
    features = build_user_features(txn, evt, users)
    STATE["features"] = features
    STATE["txn"] = txn
    STATE["evt"] = evt
    STATE["products"] = products
    print(f"✅ Features built for {len(features)} users")

@app.get("/")
def root():
    return {"service": "Feature Engineering Service", "users_with_features": len(STATE.get("features", []))}

@app.get("/features/{user_id}")
def get_user_features(user_id: str):
    """Get all computed features for a specific user."""
    features = STATE.get("features")
    if features is None:
        raise HTTPException(status_code=503, detail="Features not ready")

    row = features[features["user_id"] == user_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="User not found")

    return row.iloc[0].to_dict()

@app.get("/features/batch")
def get_batch_features(limit: int = 100):
    """Get features for multiple users."""
    features = STATE.get("features")
    if features is None:
        raise HTTPException(status_code=503, detail="Features not ready")
    return features.head(limit).to_dict(orient="records")

@app.get("/rfm/distribution")
def rfm_distribution():
    """Get RFM score distribution for all users."""
    features = STATE.get("features")
    if features is None:
        raise HTTPException(status_code=503, detail="Features not ready")

    return {
        "recency": {
            "mean": round(float(features["recency"].mean()), 2),
            "median": round(float(features["recency"].median()), 2),
            "min": int(features["recency"].min()),
            "max": int(features["recency"].max()),
        },
        "frequency": {
            "mean": round(float(features["frequency"].mean()), 2),
            "median": round(float(features["frequency"].median()), 2),
            "min": int(features["frequency"].min()),
            "max": int(features["frequency"].max()),
        },
        "monetary": {
            "mean": round(float(features["monetary"].mean()), 2),
            "median": round(float(features["monetary"].median()), 2),
            "min": round(float(features["monetary"].min()), 2),
            "max": round(float(features["monetary"].max()), 2),
        },
    }

@app.get("/channel/usage")
def channel_usage():
    """Analyze channel usage distribution."""
    txn = STATE.get("txn")
    if txn is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    ch = txn["channel"].value_counts().to_dict()
    return {"channel_usage": ch, "total_transactions": len(txn)}

@app.get("/category/affinity")
def category_affinity():
    """Top product categories by revenue."""
    txn = STATE.get("txn")
    products = STATE.get("products")
    if txn is None or products is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    merged = txn.merge(products[["product_id","category"]], on="product_id", how="left")
    aff = merged.groupby("category").agg(
        total_revenue=("amount", "sum"),
        order_count=("transaction_id", "count"),
    ).reset_index().sort_values("total_revenue", ascending=False)
    aff["total_revenue"] = aff["total_revenue"].round(2)
    return aff.to_dict(orient="records")

if __name__ == "__main__":
    uvicorn.run("feature_app:app", host="0.0.0.0", port=8002, reload=True)
