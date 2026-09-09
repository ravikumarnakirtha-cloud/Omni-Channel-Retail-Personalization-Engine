"""
ml_engine.py — shared data loading and feature engineering utilities
Used by the Feature Engineering Service (Week 2+)
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np

DATASETS_DIR = Path(os.getenv("DATASETS_DIR", "/app/datasets"))


def load_data():
    txn = pd.read_csv(DATASETS_DIR / "transactions.csv", parse_dates=["transaction_date"])
    evt = pd.read_csv(DATASETS_DIR / "events.csv")
    users = pd.read_csv(DATASETS_DIR / "users.csv")
    products = pd.read_csv(DATASETS_DIR / "products.csv")
    return txn, evt, users, products


def build_user_features(txn, evt, users):
    ref_date = txn["transaction_date"].max()
    rfm = txn.groupby("user_id").agg(
        recency=("transaction_date", lambda x: (ref_date - x.max()).days),
        frequency=("transaction_id", "count"),
        monetary=("amount", "sum"),
    ).reset_index()
    rfm["monetary"] = rfm["monetary"].round(2)

    channel_counts = (
        txn.groupby(["user_id", "channel"])
        .size()
        .unstack(fill_value=0)
        .add_prefix("channel_txn_")
        .reset_index()
    )

    event_counts = (
        evt.groupby(["user_id", "event_type"])
        .size()
        .unstack(fill_value=0)
        .add_prefix("event_")
        .reset_index()
    )

    features = rfm.merge(users[["user_id", "age", "gender", "channel_preference"]], on="user_id", how="left")
    features = features.merge(channel_counts, on="user_id", how="left")
    features = features.merge(event_counts, on="user_id", how="left")
    features = features.fillna(0)
    return features
