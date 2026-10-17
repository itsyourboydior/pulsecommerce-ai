"""Demand forecasting: gradient boosting on lag/seasonal features (one global model across SKUs),
compared in a backtest against two naive baselines. The LLM is NOT used for forecasting."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

LAGS = [1, 2, 3, 4, 8, 13, 26, 52]

def add_features(df):
    df = df.sort_values(["sku", "week"]).copy()
    g = df.groupby("sku")["units"]
    for l in LAGS:
        df[f"lag{l}"] = g.shift(l)
    df["roll4"] = g.shift(1).rolling(4).mean().reset_index(level=0, drop=True)
    df["roll13"] = g.shift(1).rolling(13).mean().reset_index(level=0, drop=True)
    df["woy"] = df["week"] % 52
    df["sin"] = np.sin(2 * np.pi * df["woy"] / 52)
    df["cos"] = np.cos(2 * np.pi * df["woy"] / 52)
    df["sku_code"] = df["sku"].str.extract(r"(\d+)").astype(int)
    return df

FEATURES = [f"lag{l}" for l in LAGS] + ["roll4", "roll13", "sin", "cos", "promo", "price", "sku_code"]

def fit(train):
    d = add_features(train).dropna(subset=FEATURES)
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0).fit(d[FEATURES], d["units"])

def forecast_ahead(model, history, horizon):
    """Recursive multi-step forecast: predict a week, append it, repeat. Assumes no promo in the future."""
    hist = history[["sku", "week", "units", "price", "promo"]].copy()
    out = []
    for h in range(horizon):
        nxt = hist.groupby("sku").agg(week=("week", "max"), price=("price", "last")).reset_index()
        nxt["week"] += 1
        nxt["units"] = np.nan
        nxt["promo"] = 0
        tmp = pd.concat([hist, nxt], ignore_index=True)
        f = add_features(tmp)
        rows = f.merge(nxt[["sku", "week"]], on=["sku", "week"])
        pred = np.maximum(0, model.predict(rows[FEATURES]))
        step = rows[["sku", "week", "price", "promo"]].copy()
        step["units"] = pred
        out.append(step)
        hist = pd.concat([hist, step], ignore_index=True)
    return pd.concat(out, ignore_index=True)

def wape(actual, pred):
    return float(np.abs(actual - pred).sum() / max(actual.sum(), 1e-9))
