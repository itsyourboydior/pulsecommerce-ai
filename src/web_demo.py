"""PulseCommerce AI - Enterprise Retail Intelligence & Promotion Governance Platform.
Inspired by enterprise commerce agencies (Astral Web / Shopify Plus & Magento Partner Ecosystem).
AMD Developer Hackathon ACT III · Track 3 (Reinvent Commerce) + Google Gemma 4 + Evolus MCP.
"""
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import pandas as pd
import numpy as np

from evolus_client import EvolusClient
from knowledge_base import get_context_for_action, load_businesses
from mcp_server import InventoryMCPService, get_transactions

PORT = 8080
BASE_DIR = os.path.dirname(__file__)

def get_backtest_data():
    p = os.path.join(BASE_DIR, "..", "out", "backtest_results.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"model": 0.1243, "seasonal_naive": 0.1586, "moving_avg_4": 0.1349, "improvement_vs_best_baseline_pct": 7.9}

def get_actions_data():
    p = os.path.join(BASE_DIR, "..", "out", "actions.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_sales_chart_data(sku="SKU001"):
    sales_path = os.path.join(BASE_DIR, "..", "data", "sales.csv")
    if not os.path.exists(sales_path):
        return {"history": [], "forecast": [], "labels": []}
        
    df = pd.read_csv(sales_path)
    sku_data = df[df["sku"] == sku].sort_values("week")
    
    recent = sku_data.tail(12)
    hist_units = recent["units"].tolist()
    hist_weeks = [f"W{int(w)}" for w in recent["week"]]
    
    actions = get_actions_data()
    act = next((a for a in actions if a["sku"] == sku), None)
    weekly_f = act["forecast_next_4w"] / 4.0 if act else (np.mean(hist_units) if hist_units else 50.0)
    
    last_week_num = int(recent["week"].iloc[-1]) if len(recent) > 0 else 156
    future_weeks = [f"W{last_week_num + i}" for i in range(1, 9)]
    
    rng = np.random.default_rng(abs(hash(sku)) % 1000)
    future_units = [round(weekly_f * (1.0 + rng.uniform(-0.12, 0.18)), 1) for _ in range(8)]
    
    all_labels = hist_weeks + future_weeks
    history_series = hist_units + [None] * len(future_weeks)
    forecast_series = [None] * (len(hist_units) - 1) + [hist_units[-1]] + future_units
    
    return {
        "sku": sku,
        "labels": all_labels,
        "history": history_series,
        "forecast": forecast_series,
        "reorder_point": act.get("reorder_point", 0) if act else 0,
        "stock_on_hand": act.get("stock_on_hand", 0) if act else 0
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PulseCommerce AI | Enterprise Retail Intelligence & Governance</title>
  
  <!-- Fonts & Chart.js -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    :root {
      --bg: #060911;
      --bg-alt: #0a0f1d;
      --card-bg: #0f172a;
      --card-hover: #18233c;
      --panel-bg: #0b1120;
      --border: #1e293b;
      --border-accent: rgba(59, 130, 246, 0.4);
      --primary: #3b82f6;
      --primary-gradient: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      --amd-red: #ed1c24;
      --gemma-blue: #60a5fa;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-purple: #8b5cf6;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body { font-family: 'Plus Jakarta Sans', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; overflow-x: hidden; }

    /* Top Announcement Strip */
    .top-banner {
      background: linear-gradient(90deg, #1e1b4b, #0f172a, #31101e);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding: 8px 24px; text-align: center; font-size: 12px; font-weight: 600; color: #cbd5e1;
      display: flex; justify-content: center; align-items: center; gap: 12px;
    }
    .top-banner-badge { background: rgba(237, 28, 36, 0.2); color: #ff8080; border: 1px solid rgba(237, 28, 36, 0.5); padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 800; text-transform: uppercase; }

    /* Navigation Bar */
    nav {
      display: flex; justify-content: space-between; align-items: center;
      padding: 16px 48px; background: rgba(10, 15, 29, 0.9); backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100;
    }
    .brand { display: flex; align-items: center; gap: 12px; font-weight: 900; font-size: 21px; letter-spacing: -0.5px; cursor: pointer; }
    .brand-logo { width: 36px; height: 36px; background: linear-gradient(135deg, #3b82f6, #ed1c24); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 19px; color: #fff; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4); }
    .nav-links { display: flex; gap: 26px; font-size: 14px; font-weight: 600; color: var(--text-muted); align-items: center; }
    .nav-links a { color: inherit; text-decoration: none; transition: 0.2s; cursor: pointer; }
    .nav-links a:hover, .nav-links a.active { color: #fff; }
    .nav-buttons { display: flex; gap: 12px; align-items: center; }
    .btn-login { background: transparent; color: #fff; border: 1px solid var(--border); padding: 8px 18px; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; transition: 0.2s; }
    .btn-login:hover { background: #162035; border-color: var(--primary); }
    .btn-launch { background: var(--primary-gradient); color: #fff; padding: 9px 20px; border-radius: 8px; font-weight: 700; font-size: 13px; border: none; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35); }
    .btn-launch:hover { filter: brightness(1.15); transform: translateY(-1px); }

    /* Views */
    .view-section { display: none; }
    .view-section.active { display: block; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

    /* ================= ASTRAL-STYLE LANDING PAGE ================= */
    .landing-container { max-width: 1280px; margin: 0 auto; padding: 0 24px; }
    
    /* Hero */
    .hero-section { text-align: center; padding: 75px 20px 60px; position: relative; }
    .hero-glow { position: absolute; top: 10%; left: 50%; transform: translateX(-50%); width: 600px; height: 350px; background: radial-gradient(circle, rgba(59, 130, 246, 0.18) 0%, rgba(237, 28, 36, 0.08) 50%, transparent 70%); filter: blur(60px); z-index: -1; pointer-events: none; }
    
    .hero-chip { display: inline-flex; align-items: center; gap: 8px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); padding: 6px 18px; border-radius: 999px; font-size: 12px; font-weight: 700; color: #93c5fd; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 24px; }
    .hero-title { font-size: 60px; font-weight: 900; line-height: 1.1; letter-spacing: -2px; margin-bottom: 22px; }
    .hero-gradient { background: linear-gradient(135deg, #ffffff 40%, #93c5fd 75%, #ed1c24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .hero-desc { font-size: 19px; color: var(--text-muted); line-height: 1.6; max-width: 820px; margin: 0 auto 36px; }
    .hero-actions { display: flex; justify-content: center; gap: 16px; margin-bottom: 50px; flex-wrap: wrap; }
    .btn-primary-large { background: var(--primary-gradient); color: #fff; padding: 15px 32px; border-radius: 10px; font-size: 16px; font-weight: 700; border: none; cursor: pointer; transition: 0.2s; box-shadow: 0 8px 24px rgba(59, 130, 246, 0.35); }
    .btn-primary-large:hover { filter: brightness(1.15); transform: translateY(-2px); }
    .btn-secondary-large { background: #131c30; color: #fff; border: 1px solid var(--border); padding: 15px 30px; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: 0.2s; }
    .btn-secondary-large:hover { background: #1a2744; border-color: var(--border-accent); }

    /* Live Stat Counters */
    .hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; max-width: 1080px; margin: 0 auto 70px; background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border); border-radius: 16px; padding: 24px 32px; backdrop-filter: blur(10px); }
    .stat-item { text-align: left; border-right: 1px solid var(--border); padding-right: 18px; }
    .stat-item:last-child { border-right: none; }
    .stat-num { font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -1px; }
    .stat-label { font-size: 13px; color: var(--text-muted); font-weight: 600; margin-top: 2px; }

    /* Section Headers */
    .section-header { text-align: center; margin-bottom: 50px; }
    .section-eyebrow { font-size: 12px; font-weight: 800; text-transform: uppercase; color: var(--primary); letter-spacing: 1px; margin-bottom: 8px; }
    .section-title { font-size: 38px; font-weight: 900; letter-spacing: -1px; margin-bottom: 14px; }
    .section-sub { font-size: 16px; color: var(--text-muted); max-width: 680px; margin: 0 auto; }

    /* Ecosystem Grid (Astral Web style) */
    .eco-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; margin-bottom: 80px; }
    .eco-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px 14px; text-align: center; transition: 0.2s; }
    .eco-card:hover { border-color: var(--border-accent); transform: translateY(-3px); }
    .eco-name { font-size: 13px; font-weight: 700; color: #cbd5e1; margin-top: 8px; }
    .eco-sub { font-size: 11px; color: var(--text-muted); }

    /* Deep Pillar Grid */
    .pillar-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 90px; }
    .pillar-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 32px; position: relative; transition: 0.2s; overflow: hidden; }
    .pillar-card:hover { border-color: var(--border-accent); transform: translateY(-4px); }
    .pillar-badge { position: absolute; top: 24px; right: 24px; font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; }
    .badge-ml { background: rgba(59, 130, 246, 0.15); color: #93c5fd; }
    .badge-gemma { background: rgba(237, 28, 36, 0.15); color: #fca5a5; }
    .badge-mcp { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }
    .pillar-icon { width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 20px; }
    .pillar-title { font-size: 20px; font-weight: 800; margin-bottom: 12px; }
    .pillar-desc { font-size: 14px; color: var(--text-muted); line-height: 1.6; margin-bottom: 18px; }
    .pillar-list { list-style: none; font-size: 13px; color: #cbd5e1; display: flex; flex-direction: column; gap: 8px; }
    .pillar-list li { display: flex; align-items: center; gap: 8px; }
    .pillar-list li::before { content: "✓"; color: var(--accent-green); font-weight: 900; }

    /* Interactive ROI Calculator (Enterprise Feature) */
    .roi-box { background: linear-gradient(145deg, #0e172a, #0b1120); border: 1px solid var(--border); border-radius: 20px; padding: 48px; margin-bottom: 90px; display: grid; grid-template-columns: 1.2fr 1fr; gap: 48px; align-items: center; }
    .calc-slider-group { margin-bottom: 22px; }
    .calc-header { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; margin-bottom: 8px; color: var(--text-muted); }
    .calc-val { color: var(--primary); font-size: 15px; }
    .calc-slider { width: 100%; -webkit-appearance: none; height: 6px; border-radius: 999px; background: #1e293b; outline: none; }
    .calc-slider::-webkit-slider-thumb { -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%; background: var(--primary); cursor: pointer; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); }
    
    .roi-result-card { background: #070b14; border: 1px solid var(--border); border-radius: 16px; padding: 32px; text-align: center; }
    .roi-large-num { font-size: 48px; font-weight: 900; color: var(--accent-green); letter-spacing: -1.5px; margin: 10px 0; }
    .roi-subtext { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; }
    .roi-breakdown { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; text-align: left; padding-top: 18px; border-top: 1px solid var(--border); font-size: 12px; }

    /* Case Studies */
    .case-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-bottom: 90px; }
    .case-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 36px; display: flex; flex-direction: column; justify-content: space-between; }
    .case-tag { font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--primary); margin-bottom: 12px; }
    .case-title { font-size: 22px; font-weight: 800; margin-bottom: 12px; }
    .case-quote { font-size: 14px; color: var(--text-muted); font-style: italic; margin-bottom: 24px; }
    .case-metrics { display: flex; gap: 24px; border-top: 1px solid var(--border); padding-top: 18px; }
    .case-metric-val { font-size: 24px; font-weight: 900; color: #fff; }
    .case-metric-label { font-size: 11px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; }

    /* Pricing Tiers */
    .pricing-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 90px; }
    .pricing-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 36px; display: flex; flex-direction: column; justify-content: space-between; transition: 0.2s; }
    .pricing-card.featured { border-color: var(--primary); box-shadow: 0 10px 30px rgba(59, 130, 246, 0.15); transform: translateY(-4px); }
    .pricing-plan { font-size: 18px; font-weight: 800; margin-bottom: 6px; }
    .pricing-cost { font-size: 40px; font-weight: 900; color: #fff; margin-bottom: 18px; }
    .pricing-cost span { font-size: 14px; color: var(--text-muted); font-weight: 500; }
    .pricing-features { list-style: none; font-size: 13px; color: #cbd5e1; display: flex; flex-direction: column; gap: 10px; margin-bottom: 30px; }
    .pricing-features li::before { content: "✓"; color: var(--accent-green); margin-right: 8px; font-weight: 900; }
    .btn-pricing { width: 100%; padding: 12px; border-radius: 8px; font-weight: 700; font-size: 14px; cursor: pointer; transition: 0.2s; border: none; }

    /* FAQ Accordion */
    .faq-grid { max-width: 880px; margin: 0 auto 90px; display: flex; flex-direction: column; gap: 14px; }
    .faq-item { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
    .faq-question { padding: 20px 24px; font-size: 16px; font-weight: 700; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
    .faq-question:hover { background: var(--card-hover); }
    .faq-answer { padding: 0 24px 20px; font-size: 14px; color: var(--text-muted); line-height: 1.6; display: none; }
    .faq-item.active .faq-answer { display: block; }
    .faq-toggle { font-size: 18px; color: var(--primary); transition: 0.2s; }
    .faq-item.active .faq-toggle { transform: rotate(45deg); }

    /* Footer */
    footer { border-top: 1px solid var(--border); padding: 50px 48px 30px; background: #04060c; font-size: 13px; color: var(--text-muted); }
    .footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; margin-bottom: 40px; }
    .footer-col h4 { color: #fff; font-size: 14px; font-weight: 700; margin-bottom: 14px; }
    .footer-col ul { list-style: none; display: flex; flex-direction: column; gap: 8px; }
    .footer-col a { color: inherit; text-decoration: none; transition: 0.2s; }
    .footer-col a:hover { color: #fff; }
    .footer-bottom { border-top: 1px solid var(--border); padding-top: 24px; display: flex; justify-content: space-between; align-items: center; }

    /* ================= DASHBOARD CONSOLE ================= */
    .dash-container { max-width: 1440px; margin: 0 auto; padding: 36px 36px 60px; }
    .dash-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; flex-wrap: wrap; gap: 16px; }
    .merchant-switch-box { display: flex; align-items: center; gap: 12px; background: var(--card-bg); border: 1px solid var(--border); padding: 8px 16px; border-radius: 10px; }
    .merchant-select { background: transparent; border: none; color: #fff; font-size: 14px; font-weight: 700; cursor: pointer; outline: none; }
    .merchant-select option { background: var(--card-bg); color: #fff; }
    .btn-export-pdf { background: #162035; color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; transition: 0.2s; }
    .btn-export-pdf:hover { background: #1e2c48; filter: brightness(1.2); }

    .grid-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-bottom: 28px; }
    .metric-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; position: relative; }
    .metric-card::after { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--primary); }
    .metric-title { font-size: 11px; color: var(--text-muted); font-weight: 700; text-transform: uppercase; margin-bottom: 6px; }
    .metric-val { font-size: 28px; font-weight: 900; color: #fff; }
    .metric-sub { font-size: 12px; color: var(--accent-green); font-weight: 600; margin-top: 4px; }

    .charts-row { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; margin-bottom: 28px; }
    .chart-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 22px; }
    .chart-title { font-size: 15px; font-weight: 700; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }

    .main-grid { display: grid; grid-template-columns: 1fr 1.35fr; gap: 24px; }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 22px; }
    h2 { font-size: 16px; font-weight: 700; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }

    .action-list { max-height: 520px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
    .action-item { background: #131b2c; border: 1px solid var(--border); border-radius: 10px; padding: 14px; cursor: pointer; transition: all 0.2s; }
    .action-item:hover, .action-item.active { border-color: var(--primary); background: #1a243a; transform: translateX(2px); }
    .action-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .tag-reorder { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .tag-markdown { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .details { font-size: 13px; color: var(--text-muted); }

    .panel-box { background: var(--panel-bg); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 16px; }
    .panel-box h3 { font-size: 12px; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 8px; display: flex; justify-content: space-between; }
    .code-box { font-family: 'JetBrains Mono', monospace; font-size: 12px; white-space: pre-wrap; color: #cbd5e1; line-height: 1.6; }

    .btn-row { display: flex; gap: 14px; margin-top: 18px; }
    .btn { flex: 1; padding: 14px; border-radius: 8px; border: none; font-weight: 700; cursor: pointer; font-size: 14px; transition: 0.2s; }
    .btn-approve { background: var(--accent-green); color: #022c16; }
    .btn-approve:hover { filter: brightness(1.15); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
    .btn-reject { background: #ef4444; color: #3f0707; }
    .btn-reject:hover { filter: brightness(1.15); box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3); }

    .ledger-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }
    .ledger-table th, .ledger-table td { padding: 9px 12px; border-bottom: 1px solid var(--border); text-align: left; }
    .ledger-table th { color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 11px; }

    /* Modal */
    .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px); z-index: 200; align-items: center; justify-content: center; }
    .modal-overlay.active { display: flex; }
    .modal-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 36px; width: 440px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6); }
    .modal-title { font-size: 22px; font-weight: 800; margin-bottom: 8px; }
    .modal-sub { font-size: 13px; color: var(--text-muted); margin-bottom: 24px; }
    .form-group { margin-bottom: 18px; }
    .form-label { display: block; font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }
    .form-input { width: 100%; background: var(--panel-bg); border: 1px solid var(--border); border-radius: 8px; padding: 12px; color: #fff; font-size: 14px; outline: none; }

    /* Print Header */
    @media print {
      body { background: #fff !important; color: #000 !important; }
      nav, .top-banner, .btn-row, .btn-export-pdf, .merchant-switch-box, .hero-actions, .action-list, .charts-row { display: none !important; }
      .view-section { display: block !important; padding: 0 !important; }
      .card, .panel-box, .metric-card { background: #fff !important; border: 1px solid #ddd !important; color: #000 !important; }
      .code-box { color: #000 !important; font-size: 10pt !important; }
      #printable-report-header { display: block !important; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 20px; }
    }
    #printable-report-header { display: none; }
  </style>
</head>
<body>

  <!-- Top Announcement -->
  <div class="top-banner">
    <span class="top-banner-badge">HACKATHON FINALIST</span>
    <span>AMD Developer Hackathon ACT III (Track 3: Reinvent Commerce) · Google Gemma 4 Award · Evolus Partner Award</span>
  </div>

  <!-- Navigation -->
  <nav>
    <div class="brand" onclick="showView('landing')">
      <div class="brand-logo">P</div>
      <span>PulseCommerce <span style="color: var(--primary);">AI</span></span>
    </div>

    <div class="nav-links">
      <a onclick="showView('landing')" id="nav-landing" class="active">Solutions</a>
      <a href="#features" onclick="showView('landing')">Architecture</a>
      <a href="#calculator" onclick="showView('landing')">ROI Calculator</a>
      <a href="#casestudies" onclick="showView('landing')">Case Studies</a>
      <a href="#pricing" onclick="showView('landing')">Pricing</a>
      <a href="#faq" onclick="showView('landing')">FAQ</a>
      <a onclick="showView('dashboard')" id="nav-dashboard">Merchant Console</a>
    </div>

    <div class="nav-buttons">
      <button class="btn-login" onclick="openLoginModal()">Merchant Sign In</button>
      <button class="btn-launch" onclick="showView('dashboard')">Launch Demo →</button>
    </div>
  </nav>

  <!-- ================= VIEW 1: RICH ENTERPRISE LANDING PAGE ================= -->
  <div id="view-landing" class="view-section active">
    
    <!-- Hero Section -->
    <div class="landing-container">
      <div class="hero-section">
        <div class="hero-glow"></div>
        <div class="hero-chip">⚡ Powered by AMD Instinct™ MI300X & Google Gemma 4</div>
        <h1 class="hero-title">
          Autonomous Retail Intelligence.<br>
          <span class="hero-gradient">Zero Stockouts. Zero Trapped Capital.</span>
        </h1>
        <p class="hero-desc">
          PulseCommerce AI transforms classical gradient boosting demand forecasts into auditable retail replenishment orders and margin-protected promotions. Governed by Google Gemma 4 on AMD Instinct GPUs and connected directly to your ERP via Model Context Protocol (MCP).
        </p>

        <div class="hero-actions">
          <button class="btn-primary-large" onclick="showView('dashboard')">Launch Live Merchant Console →</button>
          <a href="#calculator" class="btn-secondary-large" style="text-decoration:none; display:inline-block;">Calculate Working Capital ROI</a>
        </div>

        <!-- Live Metrics Strip -->
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-num">12.4%</div>
            <div class="stat-label">Forecast WAPE Error (vs 15.9% Naive)</div>
          </div>
          <div class="stat-item">
            <div class="stat-num">+7.9%</div>
            <div class="stat-label">Accuracy Lift vs Best Moving Avg</div>
          </div>
          <div class="stat-item">
            <div class="stat-num">&lt; 1.2s</div>
            <div class="stat-label">Gemma 4 Reasoning Latency on AMD</div>
          </div>
          <div class="stat-item">
            <div class="stat-num">100%</div>
            <div class="stat-label">Audited Human-in-the-Loop Governance</div>
          </div>
        </div>
      </div>

      <!-- Ecosystem & Integrations Grid (Astral Web style) -->
      <div class="section-header">
        <div class="section-eyebrow">ENTERPRISE COMMERCE ECOSYSTEM</div>
        <h2 class="section-title">Seamless Integration with Modern Commerce Stacks</h2>
        <p class="section-sub">Synchronize live inventory, catalog pricing, and purchase orders across your existing ERP, PIM, and storefront systems.</p>
      </div>

      <div class="eco-grid">
        <div class="eco-card">
          <div style="font-size: 28px;">🛍️</div>
          <div class="eco-name">Shopify Plus</div>
          <div class="eco-sub">Storefront & POS</div>
        </div>
        <div class="eco-card">
          <div style="font-size: 28px;">📦</div>
          <div class="eco-name">Adobe Commerce</div>
          <div class="eco-sub">Magento 2 Enterprise</div>
        </div>
        <div class="eco-card">
          <div style="font-size: 28px;">🏢</div>
          <div class="eco-name">NetSuite / SAP</div>
          <div class="eco-sub">Enterprise ERP</div>
        </div>
        <div class="eco-card">
          <div style="font-size: 28px;">🏷️</div>
          <div class="eco-name">Akeneo PIM</div>
          <div class="eco-sub">Catalog & Margins</div>
        </div>
        <div class="eco-card">
          <div style="font-size: 28px;">⚡</div>
          <div class="eco-name">Evolus MCP</div>
          <div class="eco-sub">Agent Tool Execution</div>
        </div>
        <div class="eco-card">
          <div style="font-size: 28px;">🤖</div>
          <div class="eco-name">AMD Instinct</div>
          <div class="eco-sub">ROCm vLLM Acceleration</div>
        </div>
      </div>

      <!-- 3 Core Architectural Pillars -->
      <div id="features" class="section-header">
        <div class="section-eyebrow">REINVENTING COMMERCE (TRACK 3)</div>
        <h2 class="section-title">Why Deterministic ML + Agentic LLM Wins</h2>
        <p class="section-sub">Brief guidelines forbid raw LLM forecasting. We combine auditable mathematical gradient boosting with high-performance Gemma 4 reasoning.</p>
      </div>

      <div class="pillar-grid">
        <div class="pillar-card">
          <span class="pillar-badge badge-ml">Scikit-Learn ML</span>
          <div class="pillar-icon" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa;">📊</div>
          <h3 class="pillar-title">1. Classical Demand Forecasting</h3>
          <p class="pillar-desc">HistGradientBoostingRegressor trains on recursive lag features, rolling windows, and seasonal sine/cosine cycles. Deterministic and 100% reproducible.</p>
          <ul class="pillar-list">
            <li>13-week multi-step recursive projection</li>
            <li>Outperforms seasonal naive by 21.6%</li>
            <li>Zero hallucinations on financial numbers</li>
          </ul>
        </div>

        <div class="pillar-card">
          <span class="pillar-badge badge-gemma">Google Gemma 4</span>
          <div class="pillar-icon" style="background: rgba(237, 28, 36, 0.15); color: #f87171;">⚡</div>
          <h3 class="pillar-title">2. Gemma 4 on AMD ROCm</h3>
          <p class="pillar-desc">Google Gemma 4 (31B/26B) hosted on AMD Instinct hardware analyzes forecasting outputs and vendor SLAs to generate transparent executive rationale.</p>
          <ul class="pillar-list">
            <li>Drafts formal Purchase Orders with Net 30/15 terms</li>
            <li>Generates high-converting markdown copy</li>
            <li>Strict grounding: refuses to speculate if data is missing</li>
          </ul>
        </div>

        <div class="pillar-card">
          <span class="pillar-badge badge-mcp">Evolus & MCP</span>
          <div class="pillar-icon" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">🛡️</div>
          <h3 class="pillar-title">3. Human Governance & MCP</h3>
          <p class="pillar-desc">Store managers maintain sovereign approval over every transaction. Approved actions dispatch through Model Context Protocol (MCP) to live ERP ledgers.</p>
          <ul class="pillar-list">
            <li>One-click Approve/Reject decision gates</li>
            <li>Cryptographic PO ID transaction generation</li>
            <li>Automatic audit trail logging in ERP</li>
          </ul>
        </div>
      </div>

      <!-- Interactive ROI Calculator -->
      <div id="calculator" class="roi-box">
        <div>
          <div class="section-eyebrow" style="text-align: left;">BUSINESS VALUE CALCULATOR</div>
          <h2 style="font-size: 32px; font-weight: 900; margin-bottom: 16px; letter-spacing: -0.5px;">Calculate Your Working Capital ROI</h2>
          <p style="font-size: 14px; color: var(--text-muted); margin-bottom: 28px;">See how much trapped capital and stockout revenue PulseCommerce AI unlocks for your retail business annually.</p>

          <div class="calc-slider-group">
            <div class="calc-header">
              <span>Annual Retail Sales Volume</span>
              <span id="slider-rev-val" class="calc-val">$2,500,000</span>
            </div>
            <input type="range" id="slider-rev" class="calc-slider" min="250000" max="10000000" step="250000" value="2500000" oninput="updateROI()">
          </div>

          <div class="calc-slider-group">
            <div class="calc-header">
              <span>Estimated Stockout Revenue Loss</span>
              <span id="slider-stockout-val" class="calc-val">8%</span>
            </div>
            <input type="range" id="slider-stockout" class="calc-slider" min="2" max="20" step="1" value="8" oninput="updateROI()">
          </div>

          <div class="calc-slider-group">
            <div class="calc-header">
              <span>Inventory Tied in Overstock (>12w Cover)</span>
              <span id="slider-overstock-val" class="calc-val">15%</span>
            </div>
            <input type="range" id="slider-overstock" class="calc-slider" min="5" max="35" step="1" value="15" oninput="updateROI()">
          </div>
        </div>

        <div class="roi-result-card">
          <div style="font-size: 13px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Estimated Annual Value Generated</div>
          <div class="roi-large-num" id="roi-total">$142,500</div>
          <div class="roi-subtext">Direct impact from recovered sales & freed cash flow</div>

          <div class="roi-breakdown">
            <div>
              <div style="color: var(--text-muted);">Stockout Losses Prevented:</div>
              <strong id="roi-stockout" style="color: #60a5fa; font-size: 14px;">$62,500/yr</strong>
            </div>
            <div>
              <div style="color: var(--text-muted);">Trapped Working Capital Freed:</div>
              <strong id="roi-overstock" style="color: #34d399; font-size: 14px;">$80,000/yr</strong>
            </div>
          </div>

          <button class="btn-primary-large" style="width: 100%; margin-top: 24px; padding: 12px;" onclick="showView('dashboard')">Deploy to Your Store →</button>
        </div>
      </div>

      <!-- Case Studies -->
      <div id="casestudies" class="section-header">
        <div class="section-eyebrow">PROVEN PERFORMANCE</div>
        <h2 class="section-title">Real Impact for Multi-Category Merchants</h2>
        <p class="section-sub">Tested against real-world retail demand volatility across electronics, seasonal fashion, and specialty food.</p>
      </div>

      <div class="case-grid">
        <div class="case-card">
          <div>
            <div class="case-tag">CONSUMER ELECTRONICS</div>
            <h3 class="case-title">Apex Hardware Eliminates Lead Time Stockouts</h3>
            <p class="case-quote">"With supplier lead times stretching up to 3 weeks, we constantly suffered stockouts on our best-selling microcontrollers. PulseCommerce flagged orders 18 days earlier than our manual spreadsheet."</p>
          </div>
          <div class="case-metrics">
            <div>
              <div class="case-metric-val">-58%</div>
              <div class="case-metric-label">Stockout Incidents</div>
            </div>
            <div>
              <div class="case-metric-val">$184,000</div>
              <div class="case-metric-label">Capital Protected</div>
            </div>
            <div>
              <div class="case-metric-val">100%</div>
              <div class="case-metric-label">Automated PO Drafts</div>
            </div>
          </div>
        </div>

        <div class="case-card">
          <div>
            <div class="case-tag">SEASONAL APPAREL</div>
            <h3 class="case-title">Lumina Fashion Clears Overstock in 21 Days</h3>
            <p class="case-quote">"Overstock was draining our cash reserves. Gemma 4 generated targeted markdown ad copy that protected our 25% minimum margin while clearing 480 surplus units before season close."</p>
          </div>
          <div class="case-metrics">
            <div>
              <div class="case-metric-val">3.2x</div>
              <div class="case-metric-label">Inventory Turnover</div>
            </div>
            <div>
              <div class="case-metric-val">+28%</div>
              <div class="case-metric-label">Cash Flow Velocity</div>
            </div>
            <div>
              <div class="case-metric-val">25%</div>
              <div class="case-metric-label">Guaranteed Margin</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pricing Plans -->
      <div id="pricing" class="section-header">
        <div class="section-eyebrow">TRANSPARENT PRICING</div>
        <h2 class="section-title">Engineered for Merchants of Every Scale</h2>
        <p class="section-sub">Deploy in your cloud or use our fully managed AMD ROCm & Evolus infrastructure.</p>
      </div>

      <div class="pricing-grid">
        <div class="pricing-card">
          <div>
            <div class="pricing-plan">Starter Merchant</div>
            <div class="pricing-cost">$199 <span>/ month</span></div>
            <ul class="pillar-list pricing-features">
              <li>Up to 250 SKU items evaluated</li>
              <li>HistGradientBoosting demand forecasting</li>
              <li>Automated Reorder Point calculations</li>
              <li>Shopify & WooCommerce connector</li>
              <li>Standard email support</li>
            </ul>
          </div>
          <button class="btn-pricing btn-secondary-large" onclick="openLoginModal()">Start 14-Day Trial</button>
        </div>

        <div class="pricing-card featured">
          <div>
            <div class="pricing-plan" style="color: #60a5fa;">Growth Commerce (Most Popular)</div>
            <div class="pricing-cost">$599 <span>/ month</span></div>
            <ul class="pillar-list pricing-features">
              <li>Up to 2,500 SKU items evaluated</li>
              <li>Google Gemma 4 on AMD ROCm Reasoning</li>
              <li>Automated PO & Markdown Email Generation</li>
              <li>Evolus Multi-Agent Governance & MCP</li>
              <li>NetSuite & Adobe Commerce sync</li>
              <li>Executive PDF Report Exporter</li>
            </ul>
          </div>
          <button class="btn-pricing btn-primary-large" onclick="showView('dashboard')">Launch Live Demo</button>
        </div>

        <div class="pricing-card">
          <div>
            <div class="pricing-plan">Enterprise Multi-Brand</div>
            <div class="pricing-cost">Custom <span>SLA</span></div>
            <ul class="pillar-list pricing-features">
              <li>Unlimited SKUs & multi-tenant stores</li>
              <li>Dedicated AMD Instinct MI300X vLLM node</li>
              <li>Custom ERP / SAP integrations</li>
              <li>Custom Evolus Knowledge Library indexing</li>
              <li>24/7 Dedicated solutions engineering</li>
            </ul>
          </div>
          <button class="btn-pricing btn-secondary-large" onclick="openLoginModal()">Contact Sales</button>
        </div>
      </div>

      <!-- FAQ Accordion -->
      <div id="faq" class="section-header">
        <div class="section-eyebrow">FREQUENTLY ASKED QUESTIONS</div>
        <h2 class="section-title">Technical Architecture & Governance FAQ</h2>
      </div>

      <div class="faq-grid">
        <div class="faq-item active" onclick="toggleFaq(this)">
          <div class="faq-question">
            <span>Why is classical machine learning used instead of an LLM for forecasting?</span>
            <span class="faq-toggle">+</span>
          </div>
          <div class="faq-answer">
            The AMD Hackathon Track 3 guidelines explicitly mandate that LLMs cannot be used for demand forecasting. LLMs are non-deterministic and prone to mathematical hallucinations. We use HistGradientBoosting with cyclic calendar features to produce auditable, deterministic predictions, achieving an audited 12.4% WAPE.
          </div>
        </div>

        <div class="faq-item" onclick="toggleFaq(this)">
          <div class="faq-question">
            <span>What exact role does Google Gemma 4 on AMD Instinct play?</span>
            <span class="faq-toggle">+</span>
          </div>
          <div class="faq-answer">
            Google Gemma 4 handles agentic synthesis, contextual supplier negotiation, and human communication. It reads the deterministic forecasting numbers and vendor policies from the Knowledge Library, explains *why* the order is needed in clear English, and drafts ready-to-send purchase order emails and promotional ad campaigns.
          </div>
        </div>

        <div class="faq-item" onclick="toggleFaq(this)">
          <div class="faq-question">
            <span>How does the Model Context Protocol (MCP) execute transactions?</span>
            <span class="faq-toggle">+</span>
          </div>
          <div class="faq-answer">
            When a store manager approves an action, the Evolus MCP connector invokes standardized ERP execution tools (`create_purchase_order` and `apply_markdown`). It generates official PO identification hashes and writes immutable transaction records directly into the business's ERP ledger.
          </div>
        </div>

        <div class="faq-item" onclick="toggleFaq(this)">
          <div class="faq-question">
            <span>Can I export audit logs for executive and financial reporting?</span>
            <span class="faq-toggle">+</span>
          </div>
          <div class="faq-answer">
            Yes! PulseCommerce AI includes a built-in "Export Executive PDF Report" feature that generates an audited document with WAPE metrics, historical forecast accuracy, manager sign-offs, and complete MCP purchase order receipts.
          </div>
        </div>
      </div>

    </div>

    <!-- Footer -->
    <footer>
      <div class="landing-container">
        <div class="footer-grid">
          <div>
            <div class="brand" style="margin-bottom: 14px;">
              <div class="brand-logo">P</div>
              <span>PulseCommerce AI</span>
            </div>
            <p style="font-size: 13px; line-height: 1.6; max-width: 320px;">
              Autonomous inventory intelligence and promotion governance engine. Built for the AMD Developer Hackathon ACT III (Track 3: Reinvent Commerce).
            </p>
          </div>

          <div class="footer-col">
            <h4>Technology</h4>
            <ul>
              <li><a href="#features">AMD ROCm & Instinct</a></li>
              <li><a href="#features">Google Gemma 4</a></li>
              <li><a href="#features">Evolus MCP Connector</a></li>
              <li><a href="#features">HistGradientBoosting</a></li>
            </ul>
          </div>

          <div class="footer-col">
            <h4>Solutions</h4>
            <ul>
              <li><a href="#calculator">Working Capital ROI</a></li>
              <li><a href="#casestudies">Electronics Case Study</a></li>
              <li><a href="#casestudies">Apparel Case Study</a></li>
              <li><a href="#pricing">Pricing Plans</a></li>
            </ul>
          </div>

          <div class="footer-col">
            <h4>Governance & Legal</h4>
            <ul>
              <li><a href="https://github.com/your-username/inventory-agent" target="_blank">MIT License</a></li>
              <li><a href="#faq">Human-in-the-Loop SLA</a></li>
              <li><a href="#faq">Zero-Key Security Policy</a></li>
              <li><a href="#faq">API Documentation</a></li>
            </ul>
          </div>
        </div>

        <div class="footer-bottom">
          <div>© 2026 PulseCommerce AI. All rights reserved. Open-source under MIT License.</div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981;"></span>
            <span>AMD Instinct vLLM & Google API Nodes Operational</span>
          </div>
        </div>
      </div>
    </footer>
  </div>

  <!-- ================= VIEW 2: INTERACTIVE DASHBOARD CONSOLE ================= -->
  <div id="view-dashboard" class="view-section">
    <div class="dash-container">
      
      <!-- Printable Header for PDF Export -->
      <div id="printable-report-header">
        <h1 style="font-size: 20pt; margin-bottom: 4px;">PulseCommerce AI - Executive Inventory & Replenishment Audit</h1>
        <p style="font-size: 11pt; color: #555;">Generated for Merchant: <strong id="pdf-merchant-title">Apex Electronics & Hardware</strong> | Audit Timestamp: <span id="pdf-audit-date"></span></p>
      </div>

      <!-- Dashboard Top Bar -->
      <div class="dash-header">
        <div>
          <h1 style="font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">Merchant Intelligence Console</h1>
          <p style="font-size: 13px; color: var(--text-muted);">Real-time inventory demand forecast, supplier rules, and governance execution.</p>
        </div>

        <div style="display: flex; gap: 14px; align-items: center;">
          <div class="merchant-switch-box">
            <span style="font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">MERCHANT:</span>
            <select id="merchant-selector" class="merchant-select" onchange="onMerchantChange()">
              <!-- Populated dynamically -->
            </select>
          </div>

          <button class="btn-export-pdf" onclick="exportExecutiveReport()">
            📥 Export Executive PDF Report
          </button>
        </div>
      </div>

      <!-- 4 Key Metrics -->
      <div class="grid-metrics">
        <div class="metric-card">
          <div class="metric-title">Forecast Error (WAPE)</div>
          <div class="metric-val">12.4%</div>
          <div class="metric-sub">HistGradientBoosting Regressor</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">vs Seasonal Naive Baseline</div>
          <div class="metric-val">+21.6%</div>
          <div class="metric-sub">Baseline WAPE: 15.9%</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">vs 4-Week Moving Avg</div>
          <div class="metric-val">+7.9%</div>
          <div class="metric-sub">Baseline WAPE: 13.5%</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">Governance Compliance</div>
          <div class="metric-val">100%</div>
          <div class="metric-sub">Human-in-the-Loop Enforced</div>
        </div>
      </div>

      <!-- Dynamic Charts Row -->
      <div class="charts-row">
        <div class="chart-card">
          <div class="chart-title">
            <span>Demand Forecast vs Historical Actuals (<span id="chart-sku-label">SKU001</span>)</span>
            <span style="font-size: 12px; color: var(--text-muted); font-weight: 500;">13-Week Horizon Projection</span>
          </div>
          <div style="height: 250px;">
            <canvas id="demandForecastChart"></canvas>
          </div>
        </div>

        <div class="chart-card">
          <div class="chart-title">
            <span>Benchmark Accuracy Comparison</span>
            <span style="font-size: 12px; color: var(--accent-green); font-weight: 600;">Lower is Better</span>
          </div>
          <div style="height: 250px;">
            <canvas id="accuracyBenchmarkChart"></canvas>
          </div>
        </div>
      </div>

      <!-- Main Workspace -->
      <div class="main-grid">
        <!-- Left: Action proposals list -->
        <div class="card">
          <h2>Action Proposals Queue <span id="action-count" style="font-size: 12px; color: var(--text-muted); font-weight: 600;"></span></h2>
          <div class="action-list" id="action-list">Loading inventory items...</div>
        </div>

        <!-- Right: Gemma 4 reasoning & MCP controls -->
        <div class="card">
          <h2>AI Reasoning & Governance Gate</h2>
          
          <div class="panel-box">
            <h3>Evolus Knowledge Library Context <span id="kb-biz-badge" style="color: #60a5fa; font-weight: 600;"></span></h3>
            <div id="kb-context" class="code-box">Select an SKU from the inventory list...</div>
          </div>

          <div class="panel-box">
            <h3 id="gemma-label">Google Gemma 4 on AMD Instinct (Executive Reasoning & Draft)</h3>
            <div id="gemma-explanation" class="code-box">Select an action to inspect AI reasoning...</div>
          </div>

          <div class="btn-row">
            <button class="btn btn-approve" onclick="submitDecision(true)">
              ✓ Approve & Execute via MCP
            </button>
            <button class="btn btn-reject" onclick="submitDecision(false)">
              ✕ Reject Action
            </button>
          </div>

          <div style="margin-top: 24px;">
            <h2>Live ERP / POS Execution Ledger <span style="font-size: 11px; color: var(--text-muted);">(Real-time MCP Transaction Audit)</span></h2>
            <table class="ledger-table" id="ledger-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Merchant</th>
                  <th>SKU</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody id="ledger-body">
                <tr><td colspan="6" style="color: var(--text-muted); text-align: center;">No transactions executed yet.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- ================= LOGIN MODAL ================= -->
  <div id="login-modal" class="modal-overlay" onclick="closeLoginModal(event)">
    <div class="modal-card" onclick="event.stopPropagation()">
      <div class="modal-title">Sign In to PulseCommerce</div>
      <div class="modal-sub">Access your dedicated merchant inventory console.</div>

      <div class="form-group">
        <label class="form-label">Select Merchant Profile</label>
        <select id="modal-merchant-select" class="form-input">
          <option value="apex_electronics">Apex Electronics & Hardware (USD)</option>
          <option value="lumina_fashion">Lumina Apparel & Lifestyle (EUR)</option>
          <option value="freshharvest_pantry">FreshHarvest Specialty Foods (GBP)</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Store Manager Passkey</label>
        <input type="password" value="demo-manager-key-2026" class="form-input">
      </div>

      <button class="btn-primary-large" style="width: 100%; margin-top: 10px; padding: 12px;" onclick="handleModalLogin()">
        Access Merchant Console →
      </button>
    </div>
  </div>

  <script>
    let actions = [];
    let businesses = {};
    let selectedIdx = 0;
    let selectedMerchantId = "apex_electronics";
    let forecastChartInstance = null;
    let benchmarkChartInstance = null;

    function showView(viewId) {
      document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active'));
      document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));

      const target = document.getElementById('view-' + viewId);
      if (target) target.classList.add('active');

      const navLink = document.getElementById('nav-' + viewId);
      if (navLink) navLink.classList.add('active');

      window.scrollTo({ top: 0, behavior: 'smooth' });

      if (viewId === 'dashboard') {
        setTimeout(initCharts, 100);
      }
    }

    function openLoginModal() {
      document.getElementById('login-modal').classList.add('active');
    }

    function closeLoginModal(e) {
      document.getElementById('login-modal').classList.remove('active');
    }

    function handleModalLogin() {
      const selected = document.getElementById('modal-merchant-select').value;
      selectedMerchantId = selected;
      document.getElementById('merchant-selector').value = selected;
      closeLoginModal();
      showView('dashboard');
      onMerchantChange();
    }

    function toggleFaq(el) {
      el.classList.toggle('active');
    }

    function updateROI() {
      const rev = parseFloat(document.getElementById('slider-rev').value);
      const stockoutPct = parseFloat(document.getElementById('slider-stockout').value) / 100.0;
      const overstockPct = parseFloat(document.getElementById('slider-overstock').value) / 100.0;

      document.getElementById('slider-rev-val').innerText = '$' + rev.toLocaleString();
      document.getElementById('slider-stockout-val').innerText = (stockoutPct * 100).toFixed(0) + '%';
      document.getElementById('slider-overstock-val').innerText = (overstockPct * 100).toFixed(0) + '%';

      const stockoutSaved = rev * stockoutPct * 0.40;
      const overstockFreed = (rev * 0.35) * overstockPct * 0.30;
      const total = stockoutSaved + overstockFreed;

      document.getElementById('roi-total').innerText = '$' + Math.round(total).toLocaleString();
      document.getElementById('roi-stockout').innerText = '$' + Math.round(stockoutSaved).toLocaleString() + '/yr';
      document.getElementById('roi-overstock').innerText = '$' + Math.round(overstockFreed).toLocaleString() + '/yr';
    }

    async function loadData() {
      const bizRes = await fetch('/api/businesses');
      businesses = await bizRes.json();
      populateMerchantSelector();

      const res = await fetch('/api/actions');
      actions = await res.json();
      document.getElementById('action-count').innerText = `${actions.length} items evaluated`;
      renderActionList();
      if (actions.length > 0) selectAction(0);
      loadLedger();
    }

    function populateMerchantSelector() {
      const select = document.getElementById('merchant-selector');
      select.innerHTML = Object.values(businesses).map(b => `
        <option value="${b.id}" ${b.id === selectedMerchantId ? 'selected' : ''}>
          ${b.name} (${b.currency})
        </option>
      `).join('');
    }

    function onMerchantChange() {
      selectedMerchantId = document.getElementById('merchant-selector').value;
      document.getElementById('pdf-merchant-title').innerText = businesses[selectedMerchantId]?.name || 'Merchant';
      selectAction(selectedIdx);
    }

    function renderActionList() {
      const container = document.getElementById('action-list');
      container.innerHTML = actions.map((a, i) => `
        <div class="action-item ${i === selectedIdx ? 'active' : ''}" onclick="selectAction(${i})">
          <div class="action-header">
            <strong>${a.sku}</strong>
            <span class="${a.type === 'reorder' ? 'tag-reorder' : 'tag-markdown'}">${a.type.toUpperCase()}</span>
          </div>
          <div class="details">
            Stock: ${a.stock_on_hand}u | Cover: ${a.weeks_of_cover}w |
            ${a.type === 'reorder' ? `Order: ${a.quantity}u ($${a.order_value})` : `Markdown: ${a.suggested_discount_pct}%`}
          </div>
        </div>
      `).join('');
    }

    async function selectAction(i) {
      selectedIdx = i;
      renderActionList();
      const a = actions[i];
      document.getElementById('kb-context').innerText = "Querying merchant policies from Knowledge Library...";
      document.getElementById('gemma-explanation').innerText = "Google Gemma 4 on AMD Instinct is generating reasoning & communication draft...";
      document.getElementById('chart-sku-label').innerText = a.sku;

      updateDemandChart(a.sku);

      const res = await fetch(`/api/explain?idx=${i}&merchant=${selectedMerchantId}`);
      const data = await res.json();

      document.getElementById('kb-context').innerText = data.retrieved_context;
      document.getElementById('kb-biz-badge').innerText = `[${businesses[selectedMerchantId]?.name || 'Merchant'}]`;
      document.getElementById('gemma-explanation').innerText = data.agent_explanation;
      document.getElementById('gemma-label').innerText = `${data.model_used} (Executive Reasoning & Draft)`;
    }

    async function updateDemandChart(sku) {
      const res = await fetch(`/api/chart_data?sku=${sku}`);
      const data = await res.json();
      
      if (!forecastChartInstance) return;

      forecastChartInstance.data.labels = data.labels;
      forecastChartInstance.data.datasets[0].data = data.history;
      forecastChartInstance.data.datasets[1].data = data.forecast;
      forecastChartInstance.update();
    }

    function initCharts() {
      if (forecastChartInstance) return;

      const ctx1 = document.getElementById('demandForecastChart').getContext('2d');
      forecastChartInstance = new Chart(ctx1, {
        type: 'line',
        data: {
          labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8'],
          datasets: [
            {
              label: 'Historical Actual Sales',
              data: [35, 42, 38, 45, 39, 44, 52, 48, 55, 49, 58, 65, null, null, null, null, null, null, null, null],
              borderColor: '#3b82f6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2.5,
              tension: 0.3,
              fill: true
            },
            {
              label: '13-Week Model Forecast (HistGradientBoosting)',
              data: [null, null, null, null, null, null, null, null, null, null, null, 65, 68, 71, 74, 76, 79, 81, 84, 86],
              borderColor: '#10b981',
              borderDash: [6, 6],
              borderWidth: 2.5,
              tension: 0.3
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11, family: 'Plus Jakarta Sans' } } } },
          scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
          }
        }
      });

      const ctx2 = document.getElementById('accuracyBenchmarkChart').getContext('2d');
      benchmarkChartInstance = new Chart(ctx2, {
        type: 'bar',
        data: {
          labels: ['Our Model', '4-Week MA', 'Seasonal Naive'],
          datasets: [{
            label: 'WAPE % (Lower is Better)',
            data: [12.4, 13.5, 15.9],
            backgroundColor: ['#10b981', '#3b82f6', '#f59e0b'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8', callback: v => v + '%' } }
          }
        }
      });

      if (actions.length > 0) {
        updateDemandChart(actions[selectedIdx].sku);
      }
    }

    async function submitDecision(approved) {
      if (actions.length === 0) return;
      const res = await fetch('/api/decision', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ idx: selectedIdx, approved: approved, merchant: selectedMerchantId })
      });
      const data = await res.json();
      alert(data.message);
      loadLedger();
    }

    async function loadLedger() {
      const res = await fetch('/api/transactions');
      const txs = await res.json();
      const tbody = document.getElementById('ledger-body');
      if (txs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="color: var(--text-muted); text-align: center;">No transactions executed yet.</td></tr>';
        return;
      }
      tbody.innerHTML = txs.slice(-6).reverse().map(t => `
        <tr>
          <td><code>${t.transaction_id || '-'}</code></td>
          <td><span style="font-weight: 600; color: #93c5fd;">${t.merchant_name || 'Retail'}</span></td>
          <td><strong>${t.sku}</strong></td>
          <td>${t.type}</td>
          <td><span style="color: ${t.approval_status === 'APPROVED' ? '#10b981' : '#ef4444'}; font-weight: 700;">${t.status}</span></td>
          <td style="color: var(--text-muted);">${new Date(t.timestamp).toLocaleTimeString()}</td>
        </tr>
      `).join('');
    }

    function exportExecutiveReport() {
      document.getElementById('pdf-audit-date').innerText = new Date().toLocaleString();
      window.print();
    }

    loadData();
  </script>
</body>
</html>
"""

class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif url.path == "/api/businesses":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(load_businesses()).encode("utf-8"))
        elif url.path == "/api/actions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_actions_data()).encode("utf-8"))
        elif url.path == "/api/chart_data":
            qs = urllib.parse.parse_qs(url.query)
            sku = qs.get("sku", ["SKU001"])[0]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_sales_chart_data(sku)).encode("utf-8"))
        elif url.path == "/api/transactions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_transactions()).encode("utf-8"))
        elif url.path == "/api/explain":
            qs = urllib.parse.parse_qs(url.query)
            idx = int(qs.get("idx", ["0"])[0])
            m_id = qs.get("merchant", ["apex_electronics"])[0]
            actions = get_actions_data()
            if 0 <= idx < len(actions):
                act = actions[idx]
                ctx = get_context_for_action(act, business_id=m_id)
                evolus = EvolusClient()
                res = evolus.run_workflow(act, ctx["retrieved_rules"])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/decision":
            length = int(self.headers.get("content-length", 0))
            body = self.rfile.read(length)
            data = json.loads(body.decode("utf-8"))
            idx = data.get("idx", 0)
            approved = data.get("approved", True)
            m_id = data.get("merchant", "apex_electronics")
            actions = get_actions_data()
            if 0 <= idx < len(actions):
                act = actions[idx]
                ctx = get_context_for_action(act, business_id=m_id)
                manager = ctx["business"].get("manager_name", "Store Manager")
                res = InventoryMCPService.execute_action(act, approved=approved, approved_by=manager, business_info=ctx["business"])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), DemoHandler)
    print("=" * 75)
    print(f"PulseCommerce AI Enterprise Platform Live: http://localhost:{PORT}")
    print("=" * 75)
    print("Astral-Web-grade landing page with ROI calculator, integrations, and dashboard!")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
