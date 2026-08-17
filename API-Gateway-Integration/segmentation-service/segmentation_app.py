"""
Customer Segmentation Service — Week 4
K-Means clustering on RFM features to segment customers into:
  high_value | frequent_buyer | at_risk | new_customer
"""
import os, sys, pickle, json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Customer Segmentation Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DATASETS_DIR = Path(os.getenv("DATASETS_DIR", "/app/datasets"))
MODELS_DIR   = Path(os.getenv("MODELS_DIR", "/app/models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

N_CLUSTERS = int(os.getenv("N_CLUSTERS", "4"))
SEGMENT_LABELS = {0: "high_value", 1: "frequent_buyer", 2: "at_risk", 3: "new_customer"}

STATE = {}

def load_data():
    txn  = pd.read_csv(DATASETS_DIR / "transactions.csv", parse_dates=["transaction_date"])
    evt  = pd.read_csv(DATASETS_DIR / "events.csv")
    users = pd.read_csv(DATASETS_DIR / "users.csv")
    return txn, evt, users

def build_rfm(txn: pd.DataFrame, users: pd.DataFrame) -> pd.DataFrame:
    ref_date = txn["transaction_date"].max()
    rfm = txn.groupby("user_id").agg(
        recency=("transaction_date", lambda x: (ref_date - x.max()).days),
        frequency=("transaction_id", "count"),
        monetary=("amount", "sum"),
    ).reset_index()
    rfm["monetary"] = rfm["monetary"].round(2)
    # Merge user metadata
    rfm = rfm.merge(users[["user_id","registration_date","channel_preference"]], on="user_id", how="left")
    return rfm

def train_kmeans(rfm: pd.DataFrame) -> tuple:
    features = rfm[["recency","frequency","monetary"]].fillna(0)
    scaler = StandardScaler()
    X = scaler.fit_transform(features)
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    rfm["cluster"] = km.fit_predict(X)
    # Label clusters by monetary desc
    cluster_means = rfm.groupby("cluster")["monetary"].mean().sort_values(ascending=False)
    label_map = {old: SEGMENT_LABELS[i] for i, old in enumerate(cluster_means.index)}
    rfm["segment"] = rfm["cluster"].map(label_map)
    return rfm, km, scaler, label_map

@app.on_event("startup")
async def startup():
    print("🔄 Segmentation service loading data & training K-Means...")
    txn, evt, users = load_data()
    rfm_data = build_rfm(txn, users)
    rfm, km, scaler, label_map = train_kmeans(rfm_data)
    STATE["rfm"] = rfm
    STATE["km"] = km
    STATE["scaler"] = scaler
    STATE["label_map"] = label_map
    # Persist model
    with open(MODELS_DIR / "kmeans.pkl", "wb") as f:
        pickle.dump({"km": km, "scaler": scaler, "label_map": label_map}, f)
    counts = rfm["segment"].value_counts().to_dict()
    print(f"✅ Segmented {len(rfm)} users: {counts}")

@app.get("/")
def root():
    rfm = STATE.get("rfm")
    if rfm is None:
        return {"service": "Segmentation Service", "status": "loading"}
    return {"service": "Segmentation Service",
            "users_segmented": len(rfm),
            "segments": rfm["segment"].value_counts().to_dict()}

@app.get("/segment/{user_id}")
def get_segment(user_id: str):
    rfm = STATE.get("rfm")
    if rfm is None:
        raise HTTPException(503, "Model not ready")
    row = rfm[rfm["user_id"] == user_id]
    if row.empty:
        raise HTTPException(404, "User not found or no transactions")
    r = row.iloc[0]
    return {
        "user_id": user_id,
        "segment": r["segment"],
        "cluster_id": int(r["cluster"]),
        "recency_days": int(r["recency"]),
        "frequency": int(r["frequency"]),
        "monetary": float(r["monetary"]),
    }

@app.get("/segments/summary")
def segments_summary():
    rfm = STATE.get("rfm")
    if rfm is None:
        raise HTTPException(503, "Model not ready")
    summary = rfm.groupby("segment").agg(
        count=("user_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum"),
    ).reset_index()
    summary = summary.round(2)
    return summary.to_dict(orient="records")

@app.get("/segments/distribution")
def segments_distribution():
    rfm = STATE.get("rfm")
    if rfm is None:
        raise HTTPException(503, "Model not ready")
    dist = rfm["segment"].value_counts()
    return {"total": len(rfm), "distribution": dist.to_dict(),
            "percentages": (dist / len(rfm) * 100).round(1).to_dict()}

@app.get("/rfm/top-users")
def top_users(segment: str = "high_value", limit: int = 10):
    rfm = STATE.get("rfm")
    if rfm is None:
        raise HTTPException(503, "Model not ready")
    filtered = rfm[rfm["segment"] == segment].sort_values("monetary", ascending=False).head(limit)
    return filtered[["user_id","segment","recency","frequency","monetary"]].to_dict(orient="records")

if __name__ == "__main__":
    uvicorn.run("segmentation_app:app", host="0.0.0.0", port=8004, reload=True)
