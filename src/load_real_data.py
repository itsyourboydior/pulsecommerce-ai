"""Real Dataset Ingestion Utility (M5 Forecasting or Online Retail II).
Converts daily transaction datasets into the weekly schema required by the model:
Columns: sku, week, units, price, promo
And generates corresponding data/inventory.csv.
"""
import os
import argparse
import numpy as np
import pandas as pd

SALES_OUT = os.path.join(os.path.dirname(__file__), "..", "data", "sales.csv")
INV_OUT = os.path.join(os.path.dirname(__file__), "..", "data", "inventory.csv")

def process_online_retail(filepath: str, max_skus: int = 30):
    """Processes UCI Online Retail dataset (InvoiceNo, StockCode, Quantity, InvoiceDate, UnitPrice, CustomerID)."""
    print(f"Loading Online Retail data from: {filepath}")
    df = pd.read_csv(filepath, encoding="ISO-8859-1")
    
    # Clean column names
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Filter valid sales
    df = df[df["quantity"] > 0]
    df = df[df["unitprice"] > 0]
    df = df.dropna(subset=["invoicedate", "stockcode"])
    
    # Top SKUs by volume
    top_skus = df.groupby("stockcode")["quantity"].sum().nlargest(max_skus).index
    df = df[df["stockcode"].isin(top_skus)].copy()
    
    df["invoicedate"] = pd.to_datetime(df["invoicedate"])
    df["week"] = ((df["invoicedate"] - df["invoicedate"].min()).dt.days // 7).astype(int)
    
    # Aggregate to weekly level
    weekly = df.groupby(["stockcode", "week"]).agg(
        units=("quantity", "sum"),
        price=("unitprice", "mean")
    ).reset_index()
    
    weekly.rename(columns={"stockcode": "sku"}, inplace=True)
    weekly["sku"] = "SKU_" + weekly["sku"].astype(str)
    
    # Promo heuristic: if price in a given week is < 90% of SKU median price
    sku_med_price = weekly.groupby("sku")["price"].transform("median")
    weekly["promo"] = (weekly["price"] < 0.9 * sku_med_price).astype(int)
    weekly["price"] = weekly["price"].round(2)
    
    # Fill missing weeks with 0 units
    all_weeks = range(weekly["week"].min(), weekly["week"].max() + 1)
    skus = weekly["sku"].unique()
    idx = pd.MultiIndex.from_product([skus, all_weeks], names=["sku", "week"])
    weekly = weekly.set_index(["sku", "week"]).reindex(idx).reset_index()
    weekly["units"] = weekly["units"].fillna(0)
    weekly["price"] = weekly.groupby("sku")["price"].ffill().bfill()
    weekly["promo"] = weekly["promo"].fillna(0).astype(int)
    
    # Build inventory metadata
    rng = np.random.default_rng(42)
    inv_rows = []
    for s in skus:
        sku_df = weekly[weekly["sku"] == s]
        avg_weekly = max(1.0, float(sku_df["units"].tail(12).mean()))
        price = float(sku_df["price"].iloc[-1])
        lead = int(rng.choice([1, 2, 3, 4]))
        stock = round(float(rng.choice([0.5, 1.2, 4.0, 8.0, 15.0]) * avg_weekly))
        unit_cost = round(price * float(rng.uniform(0.45, 0.70)), 2)
        inv_rows.append((s, price, lead, stock, unit_cost))
        
    inv = pd.DataFrame(inv_rows, columns=["sku", "price", "lead_time_weeks", "stock_on_hand", "unit_cost"])
    
    weekly.to_csv(SALES_OUT, index=False)
    inv.to_csv(INV_OUT, index=False)
    print(f"Successfully processed {len(skus)} SKUs across {len(all_weeks)} weeks.")
    print(f"Saved: {SALES_OUT} ({len(weekly)} rows) and {INV_OUT} ({len(inv)} rows)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert real retail dataset to weekly agent format")
    parser.add_argument("--csv", type=str, help="Path to raw CSV (e.g., Online_Retail.csv)")
    parser.add_argument("--max-skus", type=int, default=30)
    args = parser.parse_args()
    
    if args.csv and os.path.exists(args.csv):
        process_online_retail(args.csv, args.max_skus)
    else:
        print("Usage: python load_real_data.py --csv path/to/Online_Retail.csv")
        print("To download Online Retail: https://archive.ics.uci.edu/ml/datasets/online+retail")
