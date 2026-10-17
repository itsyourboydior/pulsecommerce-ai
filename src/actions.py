"""Turn forecasts + stock levels into proposed actions (reorder / markdown / ok).
This is rule-based on purpose: the numbers are deterministic and auditable. Gemma (step 3) explains them."""
import json
import numpy as np
from synth_retail import make_retail
from forecast import fit, forecast_ahead

SERVICE_Z = 1.65          # ~95% service level
OVERSTOCK_WEEKS = 12      # more than this many weeks of cover -> markdown candidate
HORIZON = 13

def build_actions(sales, inv, resid_std):
    model = fit(sales)
    fc = forecast_ahead(model, sales, HORIZON)
    actions = []
    for _, r in inv.iterrows():
        f = fc[fc.sku == r.sku]["units"].values
        lead = int(r.lead_time_weeks)
        demand_lead = float(f[:lead].sum())
        safety = SERVICE_Z * resid_std[r.sku] * np.sqrt(lead)
        reorder_point = demand_lead + safety
        weekly = float(f[:4].mean())
        cover = r.stock_on_hand / max(weekly, 1e-9)
        if r.stock_on_hand < reorder_point:
            qty = int(np.ceil(demand_lead + safety + f[lead:lead + 4].sum() - r.stock_on_hand))
            a = dict(type="reorder", quantity=qty, urgency="high" if r.stock_on_hand < demand_lead else "normal",
                     order_value=round(qty * float(r.unit_cost), 2))
        elif cover > OVERSTOCK_WEEKS:
            excess = int(r.stock_on_hand - OVERSTOCK_WEEKS * weekly)
            a = dict(type="markdown", suggested_discount_pct=15 if cover < 20 else 25,
                     excess_units=excess, tied_up_capital=round(excess * float(r.unit_cost), 2))
        else:
            continue
        actions.append({"sku": r.sku, "stock_on_hand": int(r.stock_on_hand), "lead_time_weeks": lead,
                        "forecast_next_4w": round(float(f[:4].sum())), "weeks_of_cover": round(float(cover), 1),
                        "reorder_point": round(reorder_point), **a,
                        "needs_approval": True})
    return actions

if __name__ == "__main__":
    sales, inv = make_retail()
    # residual std per SKU from a holdout of the last 8 weeks (used for safety stock)
    train, test = sales[sales.week < 148], sales[sales.week >= 148]
    m = fit(train)
    p = forecast_ahead(m, train, 8).sort_values(["sku", "week"])
    t = test.sort_values(["sku", "week"]).copy()
    t["err"] = t["units"].values - p["units"].values
    resid_std = t.groupby("sku")["err"].std().to_dict()
    actions = build_actions(sales, inv, resid_std)
    json.dump(actions, open("../out/actions.json", "w"), indent=2)
    n_re = sum(a["type"] == "reorder" for a in actions)
    print(f"{len(actions)} proposed actions: {n_re} reorders, {len(actions) - n_re} markdowns")
    print(json.dumps(actions[0], indent=2))
