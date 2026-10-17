"""Rolling-origin backtest. Reports forecast error vs naive baselines: the numbers you quote in the demo."""
import json
import numpy as np
from synth_retail import make_retail
from forecast import fit, forecast_ahead, wape

HORIZON = 4
ORIGINS = [104, 116, 128, 140]   # forecast origins (weeks); the model only sees data before each one

def main():
    sales, _ = make_retail()
    res = {"model": [], "seasonal_naive": [], "moving_avg_4": []}
    for o in ORIGINS:
        train = sales[sales.week < o]
        test = sales[(sales.week >= o) & (sales.week < o + HORIZON)].sort_values(["sku", "week"])
        model = fit(train)
        pred = forecast_ahead(model, train, HORIZON).sort_values(["sku", "week"])
        res["model"].append(wape(test["units"].values, pred["units"].values))
        # baseline 1: same week last year
        ly = sales[(sales.week >= o - 52) & (sales.week < o - 52 + HORIZON)].sort_values(["sku", "week"])
        res["seasonal_naive"].append(wape(test["units"].values, ly["units"].values))
        # baseline 2: average of the last 4 weeks
        ma = train[train.week >= o - 4].groupby("sku")["units"].mean()
        ma_pred = test["sku"].map(ma).values
        res["moving_avg_4"].append(wape(test["units"].values, ma_pred))
    summary = {k: round(float(np.mean(v)), 4) for k, v in res.items()}
    summary["improvement_vs_best_baseline_pct"] = round(
        100 * (1 - summary["model"] / min(summary["seasonal_naive"], summary["moving_avg_4"])), 1)
    summary["metric"] = f"WAPE (lower is better), {HORIZON}-week horizon, {len(ORIGINS)} rolling origins"
    print(json.dumps(summary, indent=2))
    json.dump(summary, open("../out/backtest_results.json", "w"), indent=2)

if __name__ == "__main__":
    main()
