"""Synthetic weekly retail data (stand-in for M5 / Online Retail). Same columns as a real export:
sku, week, units, price, promo. Swap in real data later via load_csv()."""
import numpy as np
import pandas as pd

def make_retail(n_skus=30, weeks=156, seed=11):
    rng = np.random.default_rng(seed)
    t = np.arange(weeks)
    rows, meta = [], []
    for i in range(1, n_skus + 1):
        base = rng.uniform(20, 200)
        trend = rng.uniform(-0.1, 0.25) * base / 52          # units gained/lost per week
        amp = rng.uniform(0.05, 0.45) * base                 # seasonality strength
        phase = rng.uniform(0, 2 * np.pi)
        price = round(float(rng.uniform(5, 60)), 2)
        promo = (rng.random(weeks) < 0.08).astype(int)       # ~8% of weeks on promotion
        mean = base + trend * t + amp * np.sin(2 * np.pi * t / 52 + phase)
        mean = mean * (1 + 0.35 * promo)
        units = np.maximum(0, rng.normal(mean, 0.08 * base + 3)).round()
        for w in range(weeks):
            rows.append((f"SKU{i:03d}", w, units[w], price, promo[w]))
        lead = int(rng.choice([1, 2, 3, 4]))
        stock = float(rng.choice([0.5, 1.5, 4.0, 7.0, 20.0, 30.0]) * base)   # some understocked, some overstocked
        meta.append((f"SKU{i:03d}", price, lead, round(stock), round(price * rng.uniform(0.4, 0.7), 2)))
    df = pd.DataFrame(rows, columns=["sku", "week", "units", "price", "promo"])
    inv = pd.DataFrame(meta, columns=["sku", "price", "lead_time_weeks", "stock_on_hand", "unit_cost"])
    return df, inv

def load_csv(path):
    return pd.read_csv(path)

if __name__ == "__main__":
    df, inv = make_retail()
    df.to_csv("../data/sales.csv", index=False)
    inv.to_csv("../data/inventory.csv", index=False)
    print(df.shape, inv.shape)
