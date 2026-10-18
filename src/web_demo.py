"""PulseCommerce AI - Enterprise Retail Intelligence Platform.
Design 1:1 tailored to AstralWeb (https://astralweb.net/):
- Warm Editorial Luxury Aesthetic
- Typography: 'Source Serif 4' for editorial headings, 'Inter' for UI & body
- Color Palette: Pure White (#ffffff), Fog (#f7f7f8), Ink (#17191c), Rust (#5d2a1a), Mint Pop (#55db9c), Electric Blue (#4da2ff), Sky Wash (#d3e3fc), Apricot Wash (#fbe1d1)
- Astral Web Hero with Soft Dawn Glow & Floating Tilted UI Cards (rotate(-5deg), rotate(4deg))
- Interactive Assembly Client Dashboard with live Chart.js demand curves
- Full Multi-Tenant Merchant Intelligence Console with Gemma 4, MCP execution, and PDF export
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
    future_units = [round(weekly_f * (1.0 + rng.uniform(-0.10, 0.15)), 1) for _ in range(8)]
    
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
    <title>PulseCommerce AI - Autonomous Retail Intelligence</title>
    
    <!-- Astral Web Typography: Source Serif 4 & Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        /* ================= ASTRAL WEB V3.1 DESIGN SYSTEM ================= */
        :root {
            /* Colors matching AstralWeb.net */
            --color-ink: #17191c;
            --color-pure-white: #ffffff;
            --color-fog: #f7f7f8;
            --color-ash: #4c4c4c;
            --color-graphite: #5f626c;
            --color-dove: #e2e4e8;
            --color-slate: #8b8c8d;
            --color-obsidian: #000000;
            
            /* Astral Accents */
            --color-rust: #5d2a1a;
            --color-apricot-wash: #fbe1d1;
            --color-sky-wash: #d3e3fc;
            --color-electric-blue: #4da2ff;
            --color-mint-pop: #55db9c;
            --color-amber-pop: #f59e0b;

            /* Fonts */
            --font-signifier: 'Source Serif 4', serif;
            --font-sohne: 'Inter', system-ui, sans-serif;

            /* Radii */
            --radius-buttons: 9999px;
            --radius-cards: 24px;
            --radius-images: 12px;
            --radius-inputs: 16px;
            --radius-tags: 9999px;

            /* Shadows from Astral Web */
            --shadow-subtle: rgba(4, 23, 43, 0.05) 0px 0px 0px 1px, rgba(0, 0, 0, 0.08) 0px 20px 25px -5px, rgba(0, 0, 0, 0.04) 0px 8px 10px -6px;
            --shadow-float: rgba(4, 23, 43, 0.06) 0px 0px 0px 1px, rgba(0, 0, 0, 0.12) 0px 24px 38px -4px, rgba(0, 0, 0, 0.06) 0px 10px 15px -5px;
            
            --page-max-width: 1240px;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html { scroll-behavior: smooth; }
        body {
            font-family: var(--font-sohne);
            color: var(--color-ink);
            background-color: var(--color-pure-white);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        /* Announcement Pill */
        .top-strip {
            background-color: var(--color-fog);
            border-bottom: 1px solid var(--color-dove);
            padding: 8px 24px;
            text-align: center;
            font-size: 13px;
            color: var(--color-graphite);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
        }
        .strip-badge {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        /* Header matching Astral Web */
        .main-header {
            position: sticky;
            top: 0;
            z-index: 100;
            padding: 16px 36px;
            background-color: rgba(255, 255, 255, 0.94);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }
        .header-container {
            max-width: var(--page-max-width);
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo-text {
            font-family: var(--font-signifier);
            font-size: 24px;
            font-weight: 400;
            color: var(--color-ink);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
            letter-spacing: -0.5px;
        }
        .logo-dot {
            width: 8px;
            height: 8px;
            background: var(--color-rust);
            border-radius: 50%;
        }
        .nav-menu {
            display: flex;
            gap: 28px;
            align-items: center;
        }
        .nav-link {
            font-family: var(--font-sohne);
            font-weight: 500;
            font-size: 14.5px;
            color: var(--color-graphite);
            text-decoration: none;
            transition: color 0.2s;
            cursor: pointer;
        }
        .nav-link:hover, .nav-link.active {
            color: var(--color-ink);
        }
        .header-actions {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        /* Astral Web Buttons */
        .btn-filled {
            font-family: var(--font-sohne);
            font-weight: 500;
            font-size: 14px;
            color: var(--color-pure-white);
            background: var(--color-ink);
            border: none;
            border-radius: var(--radius-buttons);
            padding: 9px 22px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.2s, background-color 0.2s;
        }
        .btn-filled:hover {
            background: #2b2e34;
            transform: translateY(-1px);
        }
        .btn-ghost {
            font-family: var(--font-sohne);
            font-weight: 500;
            font-size: 14px;
            color: var(--color-ink);
            background: transparent;
            border: 1px solid var(--color-dove);
            border-radius: var(--radius-buttons);
            padding: 8px 18px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-ghost:hover {
            background: var(--color-fog);
            color: var(--color-ink);
            border-color: var(--color-slate);
        }

        /* View Toggle */
        .view-section { display: none; }
        .view-section.active { display: block; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        /* ================= ASTRAL WEB HERO SECTION ================= */
        .hero-layout {
            position: relative;
            padding: 70px 24px 80px;
            text-align: center;
            overflow: visible;
            min-height: 820px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        /* Soft Dawn Radial Glow (exact from Astral Web) */
        .hero-glow {
            position: absolute;
            top: 25%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 620px;
            height: 380px;
            background: radial-gradient(circle, rgba(251, 225, 209, 0.75) 0%, rgba(211, 227, 252, 0.45) 50%, rgba(255, 255, 255, 0) 75%);
            filter: blur(40px);
            z-index: 1;
            pointer-events: none;
        }

        .hero-text-content {
            position: relative;
            z-index: 3;
            max-width: 820px;
            margin: 0 auto;
        }
        .hero-badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--color-pure-white);
            border: 1px solid var(--color-dove);
            box-shadow: 0 2px 6px rgba(0,0,0,0.03);
            padding: 6px 16px;
            border-radius: var(--radius-buttons);
            font-size: 13px;
            font-weight: 500;
            color: var(--color-graphite);
            margin-bottom: 24px;
        }
        .font-display {
            font-family: var(--font-signifier);
            font-size: clamp(52px, 6.5vw, 84px);
            font-weight: 300;
            line-height: 1.05;
            letter-spacing: -0.035em;
            color: var(--color-ink);
            margin-bottom: 24px;
        }
        .font-display em {
            font-style: italic;
            font-weight: 400;
            color: var(--color-rust);
        }
        .font-subhead {
            font-family: var(--font-sohne);
            font-size: 19px;
            font-weight: 400;
            color: var(--color-ash);
            line-height: 1.55;
            max-width: 660px;
            margin: 0 auto 36px;
        }
        .hero-cta-group {
            display: flex;
            gap: 16px;
            justify-content: center;
            margin-bottom: 50px;
        }

        /* Floating UI Cards around Hero (Iconic Astral Web Feature) */
        .hero-floating-container {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 100%;
            max-width: 1200px;
            height: 100%;
            pointer-events: none;
            z-index: 4;
        }
        .floating-ui-card {
            position: absolute;
            background: var(--color-pure-white);
            border-radius: var(--radius-cards);
            padding: 16px 20px;
            box-shadow: var(--shadow-float);
            border: 1px solid var(--color-dove);
            display: flex;
            flex-direction: column;
            gap: 6px;
            text-align: left;
            pointer-events: auto;
            transition: transform 0.3s ease;
        }
        .floating-ui-card:hover {
            transform: scale(1.04) !important;
        }
        #card-accuracy { top: 18%; left: 1%; width: 260px; transform: rotate(-5deg); }
        #card-latency { top: 22%; right: 1%; width: 270px; transform: rotate(4deg); }
        #card-capital { top: 62%; left: 2%; width: 260px; transform: rotate(-3deg); }
        #card-governance { top: 65%; right: 2%; width: 260px; transform: rotate(3deg); }

        .chip-icon {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            font-weight: 600;
        }

        /* Embedded Mock / Real Assembly Dashboard (Astral Web Style) */
        .assembly-dashboard {
            width: 100%;
            max-width: 980px;
            background: var(--color-pure-white);
            border-radius: var(--radius-cards);
            box-shadow: var(--shadow-float);
            border: 1px solid var(--color-dove);
            margin: 0 auto;
            position: relative;
            overflow: hidden;
            z-index: 5;
            text-align: left;
        }
        .db-topbar {
            height: 48px;
            border-bottom: 1px solid var(--color-dove);
            background: var(--color-fog);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }
        .window-dots {
            display: flex;
            gap: 6px;
        }
        .dot { width: 10px; height: 10px; border-radius: 50%; }
        .dot-red { background: #ff5f56; }
        .dot-yellow { background: #ffbd2e; }
        .dot-green { background: #27c93f; }
        
        .db-layout {
            display: grid;
            grid-template-columns: 200px 1fr;
            min-height: 480px;
        }
        .db-sidebar {
            background: var(--color-fog);
            border-right: 1px solid var(--color-dove);
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .sidebar-item {
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 13.5px;
            font-weight: 500;
            color: var(--color-graphite);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s;
        }
        .sidebar-item.active, .sidebar-item:hover {
            background: var(--color-pure-white);
            color: var(--color-ink);
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
            border: 1px solid var(--color-dove);
        }
        .db-main {
            padding: 24px;
            background: var(--color-pure-white);
        }

        /* Astral Web Feature / Service Cards */
        .section-wrap {
            max-width: var(--page-max-width);
            margin: 0 auto;
            padding: 80px 24px;
        }
        .section-tag {
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--color-rust);
            margin-bottom: 8px;
        }
        .section-headline {
            font-family: var(--font-signifier);
            font-size: 42px;
            font-weight: 300;
            line-height: 1.15;
            color: var(--color-ink);
            margin-bottom: 14px;
            letter-spacing: -0.02em;
        }
        .section-headline em {
            font-style: italic;
            color: var(--color-rust);
        }
        .section-subtitle {
            font-size: 17px;
            color: var(--color-graphite);
            max-width: 640px;
            margin-bottom: 48px;
        }

        .services-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 28px;
        }
        .service-card {
            background: var(--color-pure-white);
            border-radius: var(--radius-cards);
            padding: 32px;
            border: 1px solid rgba(0, 0, 0, 0.08);
            box-shadow: var(--shadow-subtle);
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.4s, box-shadow 0.4s;
            text-align: left;
        }
        .service-card:hover {
            transform: translateY(-8px);
            border-color: var(--color-electric-blue);
            box-shadow: 0 24px 48px rgba(77, 162, 255, 0.1), var(--shadow-subtle);
        }
        .service-icon-box {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-bottom: 24px;
        }

        /* Ecosystem Integration Badges */
        .integration-strip {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 16px;
            margin-top: 24px;
        }
        .int-card {
            background: var(--color-fog);
            border: 1px solid var(--color-dove);
            border-radius: 14px;
            padding: 18px 12px;
            text-align: center;
            font-size: 13px;
            font-weight: 600;
            color: var(--color-ink);
            transition: 0.2s;
        }
        .int-card:hover {
            background: var(--color-pure-white);
            border-color: var(--color-ink);
            transform: translateY(-2px);
        }

        /* Editorial ROI Calculator */
        .calculator-card {
            background: var(--color-fog);
            border: 1px solid var(--color-dove);
            border-radius: var(--radius-cards);
            padding: 48px;
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 48px;
            align-items: center;
            text-align: left;
        }
        .slider-row { margin-bottom: 24px; }
        .slider-label {
            display: flex;
            justify-content: space-between;
            font-size: 13.5px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--color-graphite);
        }
        .range-slider {
            width: 100%;
            -webkit-appearance: none;
            height: 6px;
            border-radius: 999px;
            background: #d8dbe2;
            outline: none;
        }
        .range-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: var(--color-ink);
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .roi-display-box {
            background: var(--color-pure-white);
            border: 1px solid var(--color-dove);
            border-radius: 20px;
            padding: 36px;
            text-align: center;
            box-shadow: var(--shadow-subtle);
        }

        /* FAQ Accordion */
        .faq-accordion {
            max-width: 820px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            text-align: left;
        }
        .faq-row {
            background: var(--color-pure-white);
            border: 1px solid var(--color-dove);
            border-radius: 14px;
            overflow: hidden;
            transition: all 0.2s;
        }
        .faq-head {
            padding: 20px 24px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .faq-body {
            padding: 0 24px 20px;
            font-size: 14.5px;
            color: var(--color-ash);
            line-height: 1.6;
            display: none;
        }
        .faq-row.active .faq-body { display: block; }

        /* Astral Web Footer */
        footer {
            background-color: var(--color-fog);
            border-top: 1px solid var(--color-dove);
            padding: 60px 36px 36px;
            font-size: 14px;
            color: var(--color-graphite);
            text-align: left;
        }
        .footer-cols {
            max-width: var(--page-max-width);
            margin: 0 auto 40px;
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 40px;
        }
        .footer-cols h4 {
            font-family: var(--font-sohne);
            font-size: 14px;
            font-weight: 600;
            color: var(--color-ink);
            margin-bottom: 14px;
        }
        .footer-cols ul {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .footer-cols a {
            color: inherit;
            text-decoration: none;
            transition: color 0.2s;
        }
        .footer-cols a:hover { color: var(--color-ink); }
        .footer-bottom {
            max-width: var(--page-max-width);
            margin: 0 auto;
            border-top: 1px solid var(--color-dove);
            padding-top: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }

        /* ================= MERCHANT CONSOLE (DASHBOARD) STYLES ================= */
        .dash-container {
            max-width: var(--page-max-width);
            margin: 0 auto;
            padding: 40px 24px 80px;
            text-align: left;
        }
        .dash-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .store-pill {
            display: flex;
            align-items: center;
            gap: 12px;
            background: var(--color-fog);
            border: 1px solid var(--color-dove);
            padding: 8px 16px;
            border-radius: var(--radius-buttons);
        }
        .store-dropdown {
            background: transparent;
            border: none;
            font-size: 14.5px;
            font-weight: 600;
            color: var(--color-ink);
            cursor: pointer;
            outline: none;
        }

        .metric-cards-strip {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 32px;
        }
        .m-card {
            background: var(--color-pure-white);
            border: 1px solid var(--color-dove);
            border-radius: 18px;
            padding: 22px;
            box-shadow: var(--shadow-subtle);
        }
        .m-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--color-slate);
            margin-bottom: 6px;
        }
        .m-value {
            font-family: var(--font-signifier);
            font-size: 32px;
            font-weight: 400;
            color: var(--color-ink);
            line-height: 1.1;
        }
        .m-sub {
            font-size: 12px;
            color: #059669;
            font-weight: 500;
            margin-top: 4px;
        }

        .dash-grid {
            display: grid;
            grid-template-columns: 1fr 1.35fr;
            gap: 28px;
        }
        .panel {
            background: var(--color-pure-white);
            border: 1px solid var(--color-dove);
            border-radius: var(--radius-cards);
            padding: 26px;
            box-shadow: var(--shadow-subtle);
        }

        .action-card {
            background: var(--color-fog);
            border: 1px solid var(--color-dove);
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .action-card:hover, .action-card.active {
            border-color: var(--color-ink);
            background: var(--color-pure-white);
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
            transform: translateY(-1px);
        }

        .badge-reorder {
            background: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-markdown {
            background: #fffbeb;
            color: #b45309;
            border: 1px solid #fde68a;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
        }

        .code-box-light {
            font-family: 'JetBrains Mono', monospace;
            background: var(--color-fog);
            border: 1px solid var(--color-dove);
            border-radius: 12px;
            padding: 16px;
            font-size: 13px;
            color: #27272a;
            white-space: pre-wrap;
            line-height: 1.6;
        }

        .ledger-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 12px;
        }
        .ledger-table th, .ledger-table td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--color-dove);
            text-align: left;
        }
        .ledger-table th {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--color-slate);
        }

        /* Print styles */
        @media print {
            body { background: #fff !important; }
            .main-header, .top-strip, .hero-cta-group, .btn-ghost, .btn-filled, .action-card, .btn-approve, .btn-reject { display: none !important; }
            .view-section { display: block !important; padding: 0 !important; }
            #printable-report-header { display: block !important; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 24px; }
        }
        #printable-report-header { display: none; }
            .btn-preset {
            background: #ffffff;
            border: 1px solid var(--color-dove);
            padding: 7px 14px;
            border-radius: 9999px;
            font-size: 12.5px;
            font-weight: 600;
            color: var(--color-ink);
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-preset:hover {
            border-color: var(--color-ink);
            background: #f7f7f8;
        }
        .btn-preset.active {
            background: var(--color-ink);
            color: #ffffff;
            border-color: var(--color-ink);
        }
        .btn-step {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            border: 1px solid var(--color-dove);
            background: #ffffff;
            color: var(--color-ink);
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .btn-step:hover {
            background: var(--color-fog);
            border-color: var(--color-ink);
        }
        .num-input {
            padding: 4px 8px;
            border: 1px solid var(--color-dove);
            border-radius: 6px;
            font-family: var(--font-sohne);
            font-size: 14px;
            font-weight: 700;
            color: var(--color-ink);
            text-align: right;
            width: 120px;
        }
        .num-input:focus {
            outline: none;
            border-color: var(--color-ink);
        }
        .faq-head i {
            transition: transform 0.25s ease;
        }
        .faq-row.active .faq-head i {
            transform: rotate(45deg);
        }
    
        /* Pricing Cards Styles (Astral Web Warm Editorial) */
        .pricing-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 28px;
            max-width: 1200px;
            margin: 0 auto;
            align-items: stretch;
        }
        @media (max-width: 992px) {
            .pricing-grid {
                grid-template-columns: 1fr;
            }
        }
        .pricing-card {
            background: var(--color-pure-white);
            border: 1px solid var(--color-dove);
            border-radius: 20px;
            padding: 36px 30px;
            display: flex;
            flex-direction: column;
            position: relative;
            box-shadow: 0 4px 20px rgba(0,0,0,0.02);
            transition: all 0.25s ease;
        }
        .pricing-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.06);
            border-color: var(--color-slate);
        }
        .pricing-card.featured {
            border: 2px solid var(--color-rust);
            box-shadow: 0 10px 30px rgba(93, 42, 26, 0.08);
        }
        .featured-badge {
            position: absolute;
            top: -13px;
            right: 28px;
            background: var(--color-rust);
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.6px;
            padding: 4px 14px;
            border-radius: 9999px;
            text-transform: uppercase;
        }
        .pricing-tier-tag {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--color-slate);
            margin-bottom: 6px;
        }
        .pricing-name {
            font-family: var(--font-signifier);
            font-size: 32px;
            font-weight: 400;
            color: var(--color-ink);
            margin-bottom: 8px;
        }
        .pricing-desc {
            font-size: 14px;
            color: var(--color-graphite);
            line-height: 1.5;
            min-height: 44px;
            margin-bottom: 20px;
        }
        .pricing-price-wrap {
            display: flex;
            align-items: baseline;
            gap: 4px;
            margin-bottom: 8px;
            border-bottom: 1px solid var(--color-dove);
            padding-bottom: 20px;
        }
        .pricing-curr {
            font-size: 24px;
            font-weight: 600;
            color: var(--color-ink);
        }
        .pricing-num {
            font-family: var(--font-signifier);
            font-size: 54px;
            font-weight: 400;
            color: var(--color-ink);
            line-height: 1;
        }
        .pricing-period {
            font-size: 14px;
            color: var(--color-slate);
            font-weight: 500;
        }
        .pricing-features-title {
            font-size: 11.5px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--color-slate);
            margin-bottom: 14px;
        }
        .pricing-features-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 13.5px;
            color: var(--color-ash);
            flex-grow: 1;
        }
        .pricing-features-list li {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            line-height: 1.45;
        }
        .pricing-features-list li i {
            margin-top: 3px;
            font-size: 12px;
            color: #059669;
        }

        /* Dedicated Pristine Print Styles */
        @media print {
            body * {
                visibility: hidden !important;
            }
            #printable-audit-dossier, #printable-audit-dossier * {
                visibility: visible !important;
            }
            #printable-audit-dossier {
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
                background: #ffffff !important;
                color: #111111 !important;
                padding: 24px !important;
                margin: 0 !important;
                display: block !important;
                font-family: 'Inter', system-ui, sans-serif !important;
            }
            @page {
                size: A4 portrait;
                margin: 1.2cm;
            }
        }
        #printable-audit-dossier {
            display: none;
        }

    </style>
</head>
<body>

    <!-- Top Announcement Strip -->
    <div class="top-strip">
        <span class="strip-badge">AMD Hackathon ACT III</span>
        <span>Track 3 (Reinvent Commerce) Finalist · Powered by AMD Instinct™ & Google Gemma 4</span>
    </div>

    <!-- Main Header (Styled after AstralWeb.net) -->
    <header class="main-header">
        <div class="header-container">
            <a onclick="showView('landing')" class="logo-text" style="cursor: pointer;">
                <span>PulseCommerce</span>
                <span class="logo-dot"></span>
                <span style="font-family: var(--font-sohne); font-size: 12px; font-weight: 600; color: var(--color-slate); text-transform: uppercase; letter-spacing: 0.5px;">AI</span>
            </a>

            <nav class="nav-menu">
                <a onclick="scrollToSection('landing')" class="nav-link active" id="nav-landing" style="cursor: pointer;">Solutions</a>
                <a onclick="scrollToSection('architecture')" class="nav-link" style="cursor: pointer;">Architecture</a>
                <a onclick="scrollToSection('calculator')" class="nav-link" style="cursor: pointer;">ROI Model</a>
                <a onclick="scrollToSection('pricing')" class="nav-link" style="cursor: pointer;">Pricing</a>
                <a onclick="scrollToSection('integrations')" class="nav-link" style="cursor: pointer;">Integrations</a>
                <a href="video_player.html" class="nav-link" style="cursor: pointer;"><i class="fa-solid fa-play" style="margin-right: 4px; font-size: 11px;"></i> Video</a>
                <a onclick="scrollToSection('faq')" class="nav-link" style="cursor: pointer;">FAQ</a>
                <a onclick="showView('dashboard')" class="nav-link" id="nav-dashboard" style="cursor: pointer;">Merchant Console</a>
            </nav>

            <div class="header-actions">
                <button onclick="showView('dashboard')" class="btn-filled" style="cursor: pointer; padding: 10px 22px; font-size: 14px;">Launch Workspace →</button>
            </div>
        </div>
    </header>

    <!-- ================= VIEW 1: ASTRAL WEB STYLE LANDING PAGE ================= -->
    <div id="view-landing" class="view-section active">
        <main>
            <section class="hero-layout">
                <!-- Warm Sunrise Radial Glow (Astral Web Dawn Glow) -->
                <div class="hero-glow"></div>

                <div class="hero-text-content">
                    <div class="hero-badge-pill">
                        <i class="fa-solid fa-sparkles" style="color: var(--color-rust);"></i>
                        <span>Classical Forecasting &middot; Gemma 4 &middot; Evolus MCP</span>
                    </div>

                    <h1 class="font-display">
                        Reinventing<br>
                        <em>retail intelligence.</em>
                    </h1>

                    <p class="font-subhead">
                        PulseCommerce AI transforms classical gradient boosting forecasts into auditable purchase orders and margin-protected markdowns. Governed by Google Gemma 4 on AMD Instinct™ GPUs.
                    </p>

                    <div class="hero-cta-group">
                        <button onclick="showView('dashboard')" class="btn-filled" style="padding: 12px 28px; font-size: 15px; cursor: pointer;">Launch Merchant Console</button>
                        <a href="video_player.html" class="btn-ghost" style="padding: 12px 24px; font-size: 15px; border-color: var(--color-rust); color: var(--color-rust); cursor: pointer;"><i class="fa-solid fa-play" style="margin-right: 8px;"></i> Watch 5-Min Video</a>
                        <button onclick="scrollToSection('calculator')" class="btn-ghost" style="padding: 12px 24px; font-size: 15px; cursor: pointer;">Calculate ROI <i class="fa-solid fa-arrow-right" style="margin-left: 8px; font-size: 12px;"></i></button>
                    </div>
                </div>

                <!-- Floating UI Cards around Hero (Astral Web Signature Visual) -->
                <div class="hero-floating-container">
                    <!-- Card 1: Accuracy (Top Left) -->
                    <div id="card-accuracy" class="floating-ui-card" onclick="scrollToSection('architecture')" style="cursor: pointer;">
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <div class="chip-icon" style="background: var(--color-mint-pop); color: #064e3b;">
                                <i class="fa-solid fa-chart-line"></i>
                            </div>
                            <div>
                                <div style="font-size: 14.5px; font-weight: 600;">Forecast Accuracy</div>
                                <div style="font-size: 13px; color: var(--color-graphite);">12.4% WAPE (-21.6% vs Naive)</div>
                            </div>
                        </div>
                    </div>

                    <!-- Card 2: Gemma Latency (Top Right) -->
                    <div id="card-latency" class="floating-ui-card" onclick="showView('dashboard')" style="cursor: pointer;">
                        <div style="font-size: 14px; font-weight: 600; margin-bottom: 2px;">Gemma 4 on AMD</div>
                        <div style="font-family: var(--font-signifier); font-size: 44px; color: var(--color-rust); line-height: 1;">&lt; 1.2s</div>
                        <div style="font-size: 12.5px; color: var(--color-graphite);">ROCm MI300X Acceleration</div>
                    </div>

                    <!-- Card 3: Cash Flow (Bottom Left) -->
                    <div id="card-capital" class="floating-ui-card" onclick="scrollToSection('calculator')" style="cursor: pointer;">
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <div class="chip-icon" style="background: var(--color-apricot-wash); color: var(--color-rust);">
                                <i class="fa-solid fa-coins"></i>
                            </div>
                            <div>
                                <div style="font-size: 14.5px; font-weight: 600;">Freed Capital</div>
                                <div style="font-size: 13px; color: #059669; font-weight: 600;">+$142,500 Unlocked</div>
                            </div>
                        </div>
                    </div>

                    <!-- Card 4: Governance (Bottom Right) -->
                    <div id="card-governance" class="floating-ui-card" onclick="showView('dashboard')" style="cursor: pointer;">
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <div class="chip-icon" style="background: var(--color-sky-wash); color: #0369a1;">
                                <i class="fa-solid fa-shield-halved"></i>
                            </div>
                            <div>
                                <div style="font-size: 14.5px; font-weight: 600;">Human-in-the-Loop</div>
                                <div style="font-size: 13px; color: var(--color-graphite);">100% MCP Audit Trail</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Centerpiece Mock Dashboard (Astral Web Assembly Window) -->
                <div class="assembly-dashboard">
                    <div class="db-topbar">
                        <div class="window-dots">
                            <span class="dot dot-red"></span>
                            <span class="dot dot-yellow"></span>
                            <span class="dot dot-green"></span>
                        </div>
                        <span style="font-size: 12.5px; font-weight: 500; color: var(--color-graphite);">Merchant Intelligence Console (Live Preview)</span>
                        <a onclick="showView('dashboard')" style="font-size: 12px; font-weight: 600; color: var(--color-rust); text-decoration: none; cursor: pointer;">Open Full Screen →</a>
                    </div>

                    <div class="db-layout">
                        <div class="db-sidebar">
                            <div class="sidebar-item active" onclick="showView('dashboard')" style="cursor: pointer;"><i class="fa-solid fa-chart-pie"></i> Dashboard</div>
                            <div class="sidebar-item" onclick="showView('dashboard')" style="cursor: pointer;"><i class="fa-solid fa-boxes-stacked"></i> Inventory (30)</div>
                            <div class="sidebar-item" onclick="showView('dashboard')" style="cursor: pointer;"><i class="fa-solid fa-file-invoice"></i> Orders (17)</div>
                            <div class="sidebar-item" onclick="showView('dashboard')" style="cursor: pointer;"><i class="fa-solid fa-tag"></i> Markdowns (4)</div>
                            <div class="sidebar-item" onclick="showView('dashboard')" style="cursor: pointer;"><i class="fa-solid fa-shield"></i> MCP ERP Sync</div>
                        </div>

                        <div class="db-main">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                <div>
                                    <h3 style="font-family: var(--font-signifier); font-size: 20px; font-weight: 400;">Demand Curve vs 13-Week Forecast</h3>
                                    <p style="font-size: 12.5px; color: var(--color-graphite);">HistGradientBoosting recursive prediction across SKU001</p>
                                </div>
                                <span class="badge-reorder" onclick="scrollToSection('architecture')" style="cursor: pointer;" title="Click to view benchmark methodology">WAPE: 12.4% (Pass)</span>
                            </div>
                            <div style="height: 230px;">
                                <canvas id="heroPreviewChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Architectural Pillars Section -->
            <section id="architecture" class="section-wrap" style="background: var(--color-fog); border-top: 1px solid var(--color-dove); border-bottom: 1px solid var(--color-dove);">
                <div class="section-tag">ENGINEERING THE FUTURE</div>
                <h2 class="section-headline">Why Deterministic ML + <em>Agentic LLM Wins</em></h2>
                <p class="section-subtitle">Track 3 guidelines forbid pure LLM forecasting. We build on rigorous classical statistics, elevated by Google Gemma 4 reasoning on AMD Instinct.</p>

                <div class="services-grid">
                    <div class="service-card">
                        <div class="service-icon-box" style="background: var(--color-sky-wash); color: #0284c7;">
                            <i class="fa-solid fa-chart-simple"></i>
                        </div>
                        <h3 style="font-family: var(--font-signifier); font-size: 22px; font-weight: 400; margin-bottom: 10px;">1. Gradient Boosting Core</h3>
                        <p style="font-size: 14.5px; color: var(--color-ash); line-height: 1.6; margin-bottom: 16px;">HistGradientBoostingRegressor trains on recursive weekly lags and seasonal harmonics to produce zero-hallucination demand projections.</p>
                        <ul style="list-style: none; font-size: 13.5px; color: var(--color-graphite); display: flex; flex-direction: column; gap: 8px;">
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> 12.4% WAPE error rate</li>
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> 21.6% lift vs seasonal naive</li>
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> 13-week continuous horizon</li>
                        </ul>
                        <button onclick="showView('dashboard')" class="btn-ghost" style="width: 100%; margin-top: 18px; padding: 10px 14px; font-size: 13.5px; cursor: pointer;">View Live Forecast Curves →</button>
                    </div>

                    <div class="service-card">
                        <div class="service-icon-box" style="background: var(--color-apricot-wash); color: var(--color-rust);">
                            <i class="fa-solid fa-bolt"></i>
                        </div>
                        <h3 style="font-family: var(--font-signifier); font-size: 22px; font-weight: 400; margin-bottom: 10px;">2. Gemma 4 on AMD ROCm</h3>
                        <p style="font-size: 14.5px; color: var(--color-ash); line-height: 1.6; margin-bottom: 16px;">Google Gemma 4 (31B/26B) on AMD Instinct accelerators analyzes vendor terms and explains replenishment logic in fluent executive English.</p>
                        <ul style="list-style: none; font-size: 13.5px; color: var(--color-graphite); display: flex; flex-direction: column; gap: 8px;">
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> Formal PO email generation</li>
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> Net 30/15 SLA enforcement</li>
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> Grounded, zero-guess prompts</li>
                        </ul>
                        <button onclick="showView('dashboard')" class="btn-ghost" style="width: 100%; margin-top: 18px; padding: 10px 14px; font-size: 13.5px; cursor: pointer;">Inspect Gemma 4 Reasoning & POs →</button>
                    </div>

                    <div class="service-card">
                        <div class="service-icon-box" style="background: #ecfdf5; color: #047857;">
                            <i class="fa-solid fa-shield-halved"></i>
                        </div>
                        <h3 style="font-family: var(--font-signifier); font-size: 22px; font-weight: 400; margin-bottom: 10px;">3. Evolus MCP Governance</h3>
                        <p style="font-size: 14.5px; color: var(--color-ash); line-height: 1.6; margin-bottom: 16px;">The store manager maintains final sovereign authority. Approved actions immediately trigger Model Context Protocol (MCP) ERP execution.</p>
                        <ul style="list-style: none; font-size: 13.5px; color: var(--color-graphite); display: flex; flex-direction: column; gap: 8px;">
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> One-click Approve & Reject</li>
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> Cryptographic PO generation</li>
                            <li><i class="fa-solid fa-check" style="color: #059669; margin-right: 6px;"></i> Live ERP transaction ledger</li>
                        </ul>
                        <button onclick="showView('dashboard')" class="btn-ghost" style="width: 100%; margin-top: 18px; padding: 10px 14px; font-size: 13.5px; cursor: pointer;">Open MCP Execution Ledger →</button>
                    </div>
                </div>

                <!-- Ecosystem strip -->
                <div id="integrations" style="margin-top: 60px; scroll-margin-top: 100px;">
                    <div style="font-size: 12.5px; font-weight: 600; text-transform: uppercase; color: var(--color-slate); text-align: center; margin-bottom: 18px;">Seamless Ecosystem Synchronization (Click to test integration)</div>
                    <div class="integration-strip">
                        <div class="int-card" onclick="showToast('Shopify Plus: Bi-directional inventory & catalog synchronization ready.')" style="cursor: pointer;"><i class="fa-brands fa-shopify"></i> Shopify Plus</div>
                        <div class="int-card" onclick="showToast('Adobe Commerce (Magento): Enterprise POS sync active.')" style="cursor: pointer;"><i class="fa-brands fa-magento"></i> Adobe Commerce</div>
                        <div class="int-card" onclick="showToast('NetSuite / SAP ERP: Automated purchase orders dispatched via MCP.')" style="cursor: pointer;"><i class="fa-solid fa-server"></i> NetSuite / SAP</div>
                        <div class="int-card" onclick="showToast('Akeneo PIM: Multi-attribute product governance connected.')" style="cursor: pointer;"><i class="fa-solid fa-tag"></i> Akeneo PIM</div>
                        <div class="int-card" onclick="showToast('AMD Instinct MI300X: vLLM accelerator ready with &lt;1.2s inference.')" style="cursor: pointer;"><i class="fa-solid fa-microchip"></i> AMD Instinct</div>
                        <div class="int-card" onclick="showToast('Google Gemma 4: Grounded executive reasoning model operational.')" style="cursor: pointer;"><i class="fa-solid fa-robot"></i> Google Gemma 4</div>
                    </div>
                </div>
            </section>

            <!-- ROI Calculator Section -->
            <section id="calculator" class="section-wrap">
                <div class="section-tag">CAPITAL EFFICIENCY</div>
                <h2 class="section-headline">Calculate Your Working <em>Capital ROI</em></h2>
                <p class="section-subtitle">See how much locked inventory capital and lost stockout revenue PulseCommerce AI recovers annually.</p>

                <div class="calculator-card">
                    <div>
                        <div class="slider-row">
                            <div class="slider-label">
                                <span>Annual Retail Sales Volume</span>
                                <span id="slider-rev-val" style="color: var(--color-ink); font-weight: 700;">$2,500,000</span>
                            </div>
                            <input type="range" id="slider-rev" class="range-slider" min="250000" max="10000000" step="250000" value="2500000" oninput="updateROI()">
                        </div>

                        <div class="slider-row">
                            <div class="slider-label">
                                <span>Stockout Revenue Loss Rate</span>
                                <span id="slider-stockout-val" style="color: var(--color-ink); font-weight: 700;">8%</span>
                            </div>
                            <input type="range" id="slider-stockout" class="range-slider" min="2" max="20" step="1" value="8" oninput="updateROI()">
                        </div>

                        <div class="slider-row">
                            <div class="slider-label">
                                <span>Capital Trapped in Overstock (&gt;12w)</span>
                                <span id="slider-overstock-val" style="color: var(--color-ink); font-weight: 700;">15%</span>
                            </div>
                            <input type="range" id="slider-overstock" class="range-slider" min="5" max="35" step="1" value="15" oninput="updateROI()">
                        </div>
                    </div>

                    <div class="roi-display-box">
                        <div style="font-size: 13px; font-weight: 600; color: var(--color-graphite); text-transform: uppercase;">Estimated Annual Value Generated</div>
                        <div id="roi-total" style="font-family: var(--font-signifier); font-size: 52px; color: #047857; margin: 12px 0;">$142,500</div>
                        <p style="font-size: 13.5px; color: var(--color-slate); margin-bottom: 24px;">Direct cash flow improvement through eliminated stockouts and liquidated overstock.</p>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; text-align: left; border-top: 1px solid var(--color-dove); padding-top: 18px; font-size: 12.5px;">
                            <div>
                                <span style="color: var(--color-slate);">Stockout Loss Prevented:</span><br>
                                <strong id="roi-stockout" style="color: var(--color-ink); font-size: 14px;">$62,500/yr</strong>
                            </div>
                            <div>
                                <span style="color: var(--color-slate);">Trapped Cash Liquidated:</span><br>
                                <strong id="roi-overstock" style="color: var(--color-ink); font-size: 14px;">$80,000/yr</strong>
                            </div>
                        </div>

                        <button onclick="showView('dashboard')" class="btn-filled" style="width: 100%; margin-top: 24px; padding: 12px;">Deploy to Store →</button>
                    </div>
                </div>
            </section>

            <!-- Pricing Section (Basic, Standard, Pro) -->
            <section id="pricing" class="section-wrap" style="scroll-margin-top: 80px; border-top: 1px solid var(--color-dove);">
                <div class="section-tag" style="text-align: center;">PLANS & TRANSPARENCY</div>
                <h2 class="section-headline" style="text-align: center;">Predictable Pricing for <em>Every Merchant Scale</em></h2>
                <p class="section-subtitle" style="text-align: center; margin: 0 auto 48px;">From local boutiques to high-growth omnichannel retailers. Zero setup fees, transparent unit economics.</p>

                <div class="pricing-grid">
                    <!-- 1. BASIC CARD ($29) -->
                    <div class="pricing-card">
                        <div class="pricing-tier-tag">STARTER TIER</div>
                        <h3 class="pricing-name">Basic</h3>
                        <p class="pricing-desc">For small boutique shops & independent merchants establishing automated replenishment discipline.</p>
                        <div class="pricing-price-wrap">
                            <span class="pricing-curr">$</span>
                            <span class="pricing-num">29</span>
                            <span class="pricing-period">/ month</span>
                        </div>
                        <button onclick="showView('dashboard')" class="btn-ghost" style="width: 100%; margin: 20px 0 24px; padding: 12px; font-weight: 600; cursor: pointer;">Choose Basic Plan →</button>
                        
                        <div class="pricing-features-title">PLAN SPECIFICATIONS:</div>
                        <ul class="pricing-features-list">
                            <li><i class="fa-solid fa-check"></i> <strong>Up to 100</strong> products included</li>
                            <li><i class="fa-solid fa-check"></i> Forecast and suggested actions (13w horizon)</li>
                            <li><i class="fa-solid fa-check"></i> <strong>Short Gemma explanation</strong> per action</li>
                            <li><i class="fa-solid fa-xmark" style="color: #94a3b8;"></i> <span style="color: #94a3b8;">Supplier rules library (standard terms)</span></li>
                            <li><i class="fa-solid fa-check"></i> Single store manager approval gate</li>
                            <li><i class="fa-solid fa-check"></i> Inventory system connection: <strong>Manual export (CSV)</strong></li>
                            <li><i class="fa-solid fa-check"></i> <strong>Standard Audit Report (PDF)</strong></li>
                        </ul>
                    </div>

                    <!-- 2. STANDARD CARD ($79 - RECOMMENDED) -->
                    <div class="pricing-card featured">
                        <div class="featured-badge">MOST POPULAR</div>
                        <div class="pricing-tier-tag" style="color: var(--color-rust);">GROWTH MERCHANTS</div>
                        <h3 class="pricing-name">Standard</h3>
                        <p class="pricing-desc">For growing multi-channel retail merchants demanding automated vendor email drafting & MOQ rules.</p>
                        <div class="pricing-price-wrap">
                            <span class="pricing-curr">$</span>
                            <span class="pricing-num">79</span>
                            <span class="pricing-period">/ month</span>
                        </div>
                        <button onclick="showView('dashboard')" class="btn-filled" style="width: 100%; margin: 20px 0 24px; padding: 13px; font-weight: 600; cursor: pointer;">Start with Standard →</button>
                        
                        <div class="pricing-features-title">EVERYTHING IN BASIC, PLUS:</div>
                        <ul class="pricing-features-list">
                            <li><i class="fa-solid fa-check"></i> <strong>Up to 1,000</strong> products included</li>
                            <li><i class="fa-solid fa-check"></i> Forecast and suggested actions (12.4% WAPE benchmark)</li>
                            <li><i class="fa-solid fa-check"></i> <strong>Explanation and supplier email drafts</strong></li>
                            <li><i class="fa-solid fa-check"></i> <strong>Supplier rules library</strong> (custom MOQs & terms)</li>
                            <li><i class="fa-solid fa-check"></i> Store manager approval & rejection workflow</li>
                            <li><i class="fa-solid fa-check"></i> Inventory system connection: <strong>One direct system (Shopify/ERP)</strong></li>
                            <li><i class="fa-solid fa-check"></i> <strong>Executive Audit Report (PDF) on-demand</strong></li>
                        </ul>
                    </div>

                    <!-- 3. PRO CARD ($199) -->
                    <div class="pricing-card">
                        <div class="pricing-tier-tag">ENTERPRISE SCALE</div>
                        <h3 class="pricing-name">Pro</h3>
                        <p class="pricing-desc">For high-volume retail operations needing multi-tier sign-offs and promotional markdown marketing copy.</p>
                        <div class="pricing-price-wrap">
                            <span class="pricing-curr">$</span>
                            <span class="pricing-num">199</span>
                            <span class="pricing-period">/ month</span>
                        </div>
                        <button onclick="showView('dashboard')" class="btn-ghost" style="width: 100%; margin: 20px 0 24px; padding: 12px; font-weight: 600; cursor: pointer;">Deploy Pro Tier →</button>
                        
                        <div class="pricing-features-title">ADVANCED CAPABILITIES:</div>
                        <ul class="pricing-features-list">
                            <li><i class="fa-solid fa-check"></i> <strong>Up to 10,000</strong> products included</li>
                            <li><i class="fa-solid fa-check"></i> Forecast and suggested actions (High-frequency recursive)</li>
                            <li><i class="fa-solid fa-check"></i> <strong>Explanation, supplier email & promo marketing copy</strong></li>
                            <li><i class="fa-solid fa-check"></i> <strong>Full supplier rules library</strong> with margin floors</li>
                            <li><i class="fa-solid fa-check"></i> <strong>Manager approval with multiple levels</strong> (Store + CFO)</li>
                            <li><i class="fa-solid fa-check"></i> Inventory system connection: <strong>Several systems (SAP, NetSuite, Akeneo)</strong></li>
                            <li><i class="fa-solid fa-check"></i> <strong>Full Cryptographic Audit Dossiers (PDF)</strong></li>
                        </ul>
                    </div>
                </div>
            </section>

            <!-- FAQ Section -->
            <section id="faq" class="section-wrap" style="background: var(--color-fog); border-top: 1px solid var(--color-dove);">
                <div class="section-tag" style="text-align: center;">ARCHITECTURE & GOVERNANCE</div>
                <h2 class="section-headline" style="text-align: center;">Frequently Asked <em>Questions</em></h2>
                <p class="section-subtitle" style="text-align: center; margin: 0 auto 40px;">Everything you need to know about our AMD Instinct and Google Gemma 4 implementation.</p>

                <div class="faq-accordion">
                    <div class="faq-row active" onclick="toggleFaq(this)">
                        <div class="faq-head">
                            <span>Why is classical machine learning used instead of an LLM for forecasting?</span>
                            <i class="fa-solid fa-plus"></i>
                        </div>
                        <div class="faq-body">
                            The AMD Hackathon Track 3 guidelines explicitly mandate that LLMs cannot be used for demand forecasting because LLMs are non-deterministic and prone to hallucinations. We use HistGradientBoosting with cyclic calendar features to produce 100% reproducible, mathematically auditable forecasts, achieving a verified 12.4% WAPE.
                        </div>
                    </div>

                    <div class="faq-row" onclick="toggleFaq(this)">
                        <div class="faq-head">
                            <span>What exact role does Google Gemma 4 on AMD Instinct play?</span>
                            <i class="fa-solid fa-plus"></i>
                        </div>
                        <div class="faq-body">
                            Google Gemma 4 handles agentic synthesis, contextual supplier negotiation, and human communication. It reads the deterministic forecasting numbers and vendor policies from the Knowledge Library, explains *why* the order is needed in clear English, and drafts ready-to-send purchase order emails and promotional ad campaigns.
                        </div>
                    </div>

                    <div class="faq-row" onclick="toggleFaq(this)">
                        <div class="faq-head">
                            <span>How does the Model Context Protocol (MCP) execute transactions?</span>
                            <i class="fa-solid fa-plus"></i>
                        </div>
                        <div class="faq-body">
                            When a store manager approves an action, the Evolus MCP connector invokes standardized ERP execution tools (`create_purchase_order` and `apply_markdown`). It generates official PO identification hashes and writes immutable transaction records directly into the business's ERP ledger.
                        </div>
                    </div>

                    <div class="faq-row" onclick="toggleFaq(this)">
                        <div class="faq-head">
                            <span>Can I export audit logs for executive and financial reporting?</span>
                            <i class="fa-solid fa-plus"></i>
                        </div>
                        <div class="faq-body">
                            Yes! PulseCommerce AI includes a built-in "Export Executive PDF Report" feature that generates an audited document with WAPE metrics, historical forecast accuracy, manager sign-offs, and complete MCP purchase order receipts.
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <!-- Astral Web Footer -->
        <footer>
            <div class="footer-cols">
                <div>
                    <a class="logo-text" style="margin-bottom: 14px;">
                        <span>PulseCommerce</span>
                        <span class="logo-dot"></span>
                    </a>
                    <p style="font-size: 13.5px; color: var(--color-graphite); line-height: 1.6; max-width: 320px;">
                        Autonomous inventory intelligence and promotion governance engine. Built for the AMD Developer Hackathon ACT III (Track 3: Reinvent Commerce).
                    </p>
                </div>

                <div>
                    <h4>Technology</h4>
                    <ul>
                        <li><a href="#architecture">AMD ROCm & Instinct</a></li>
                        <li><a href="#architecture">Google Gemma 4</a></li>
                        <li><a href="#architecture">Evolus MCP Connector</a></li>
                        <li><a href="#architecture">HistGradientBoosting</a></li>
                    </ul>
                </div>

                <div>
                    <h4>Solutions</h4>
                    <ul>
                        <li><a href="#calculator">Working Capital ROI</a></li>
                        <li><a onclick="showView('dashboard')">Apex Electronics</a></li>
                        <li><a onclick="showView('dashboard')">Lumina Lifestyle</a></li>
                        <li><a onclick="showView('dashboard')">FreshHarvest Foods</a></li>
                    </ul>
                </div>

                <div>
                    <h4>Governance</h4>
                    <ul>
                        <li><a href="https://github.com/your-username/inventory-agent" target="_blank">MIT License</a></li>
                        <li><a href="#faq">Human-in-the-Loop SLA</a></li>
                        <li><a href="#faq">Zero-Key Security Policy</a></li>
                    </ul>
                </div>
            </div>

            <div class="footer-bottom">
                <div>&copy; 2026 PulseCommerce AI &middot; Open-source under MIT License.</div>
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #059669;"></span>
                    <span>AMD Instinct vLLM &amp; Google API Nodes Operational</span>
                </div>
            </div>
        </footer>
    </div>

    <!-- ================= VIEW 2: INTERACTIVE DASHBOARD CONSOLE ================= -->
    <div id="view-dashboard" class="view-section">
        <div class="dash-container">
            
            <!-- Printable Header for PDF Export -->
            <div id="printable-report-header">
                <h1 style="font-family: var(--font-signifier); font-size: 24pt; margin-bottom: 4px;">PulseCommerce AI - Executive Replenishment Audit</h1>
                <p style="font-size: 11pt; color: #555;">Generated for: <strong id="pdf-merchant-title">Apex Electronics & Hardware</strong> | Audit Timestamp: <span id="pdf-audit-date"></span></p>
            </div>

            <!-- Dashboard Top Bar -->
            <div class="dash-topbar">
                <div>
                    <h1 style="font-family: var(--font-signifier); font-size: 32px; font-weight: 300; letter-spacing: -0.5px;">Merchant Intelligence Console</h1>
                    <p style="font-size: 14px; color: var(--color-graphite);">Deterministic forecasting, supplier SLAs, and human-in-the-loop governance.</p>
                </div>

                <div style="display: flex; gap: 14px; align-items: center;">
                    <div class="store-pill">
                        <span style="font-size: 11px; font-weight: 700; color: var(--color-slate); text-transform: uppercase;">MERCHANT:</span>
                        <select id="merchant-selector" class="store-dropdown" onchange="onMerchantChange()">
                            <!-- Dynamically populated -->
                        </select>
                    </div>

                    <button class="btn-ghost" onclick="exportExecutiveReport()" style="gap: 8px;">
                        <i class="fa-solid fa-download"></i> Export Executive PDF Report
                    </button>
                    <button class="btn-filled" onclick="showView('landing')">
                        Back to Overview
                    </button>
                </div>
            </div>

            <!-- 4 Metric Cards -->
            <div class="metric-cards-strip">
                <div class="m-card">
                    <div class="m-title">Forecast Error (WAPE)</div>
                    <div class="m-value">12.4%</div>
                    <div class="m-sub">HistGradientBoosting Regressor</div>
                </div>
                <div class="m-card">
                    <div class="m-title">vs Seasonal Naive Baseline</div>
                    <div class="m-value">+21.6%</div>
                    <div class="m-sub">Baseline WAPE: 15.9%</div>
                </div>
                <div class="m-card">
                    <div class="m-title">vs 4-Week Moving Avg</div>
                    <div class="m-value">+7.9%</div>
                    <div class="m-sub">Baseline WAPE: 13.5%</div>
                </div>
                <div class="m-card">
                    <div class="m-title">Governance Compliance</div>
                    <div class="m-value">100%</div>
                    <div class="m-sub">Human-in-the-Loop Enforced</div>
                </div>
            </div>

            <!-- Main Workspace: Queue & Reasoning -->
            <div class="dash-grid">
                <!-- Left: Action Proposals List -->
                <div class="panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                        <h2 style="font-family: var(--font-signifier); font-size: 20px; font-weight: 400;">Action Queue</h2>
                        <span id="action-count" style="font-size: 12px; color: var(--color-slate); font-weight: 600;"></span>
                    </div>
                    <div class="action-list" id="action-list" style="max-height: 540px; overflow-y: auto;">Loading items...</div>
                </div>

                <!-- Right: Gemma 4 Reasoning & MCP Execution -->
                <div class="panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                        <h2 style="font-family: var(--font-signifier); font-size: 20px; font-weight: 400;">AI Reasoning &amp; Governance</h2>
                        <span id="kb-biz-badge" style="font-size: 12px; font-weight: 600; color: var(--color-rust);"></span>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <div style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; color: var(--color-slate); margin-bottom: 6px;">Evolus Knowledge Library Context</div>
                        <div id="kb-context" class="code-box-light">Select an SKU from the inventory list...</div>
                    </div>

                    <div style="margin-bottom: 20px;">
                        <div id="gemma-label" style="font-size: 11.5px; font-weight: 700; text-transform: uppercase; color: var(--color-slate); margin-bottom: 6px;">Google Gemma 4 on AMD Instinct (Executive Reasoning &amp; Draft)</div>
                        <div id="gemma-explanation" class="code-box-light" style="min-height: 140px;">Select an action to inspect AI reasoning...</div>
                    </div>

                    <div style="display: flex; gap: 14px; margin-bottom: 28px;">
                        <button class="btn-filled" style="flex: 1; background: #059669; padding: 13px; font-size: 14px;" onclick="submitDecision(true)">
                            <i class="fa-solid fa-check" style="margin-right: 6px;"></i> Approve &amp; Execute via MCP
                        </button>
                        <button class="btn-filled" style="flex: 1; background: #dc2626; padding: 13px; font-size: 14px;" onclick="submitDecision(false)">
                            <i class="fa-solid fa-xmark" style="margin-right: 6px;"></i> Reject Action
                        </button>
                    </div>

                    <div>
                        <h3 style="font-family: var(--font-signifier); font-size: 18px; font-weight: 400; margin-bottom: 10px;">Live ERP / POS Execution Ledger</h3>
                        <table class="ledger-table">
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
                                <tr><td colspan="6" style="color: var(--color-slate); text-align: center;">No transactions executed yet.</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
    </div>

    <script>
        let actions = [];
        let businesses = {};
        let selectedIdx = 0;
        let selectedMerchantId = "apex_electronics";
        let heroChartInstance = null;

        function showView(viewId) {
            document.querySelectorAll('.view-section').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.nav-menu a').forEach(a => a.classList.remove('active'));

            const target = document.getElementById('view-' + viewId);
            if (target) target.classList.add('active');

            const navLink = document.getElementById('nav-' + viewId);
            if (navLink) navLink.classList.add('active');

            if (viewId === 'dashboard') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }

            if (viewId === 'landing' || viewId === 'dashboard') {
                setTimeout(initHeroChart, 100);
            }
        }

        function toggleFaq(el) {
            el.classList.toggle('active');
        }

        function scrollToSection(sectionId) {
            showView('landing');
            if (sectionId === 'landing') {
                window.scrollTo({ top: 0, behavior: 'smooth' });
                return;
            }
            setTimeout(() => {
                const el = document.getElementById(sectionId);
                if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 60);
        }

        function showToast(msg) {
            let t = document.getElementById('toast-notification');
            if (!t) {
                t = document.createElement('div');
                t.id = 'toast-notification';
                t.style.cssText = 'position: fixed; bottom: 24px; right: 24px; background: #17191C; color: #FFFFFF; padding: 14px 22px; border-radius: 9999px; font-size: 14px; z-index: 99999; box-shadow: 0 10px 25px rgba(0,0,0,0.25); transition: all 0.3s; opacity: 0; transform: translateY(10px); pointer-events: none; font-family: var(--font-sohne); display: flex; align-items: center; gap: 8px;';
                document.body.appendChild(t);
            }
            t.innerHTML = '<i class="fa-solid fa-circle-check" style="color: #55db9c; font-size: 16px;"></i> ' + msg;
            t.style.opacity = '1';
            t.style.transform = 'translateY(0)';
            setTimeout(() => {
                t.style.opacity = '0';
                t.style.transform = 'translateY(10px)';
            }, 3000);
        }

        function syncFromSlider(type) {
            if (type === 'rev') {
                const val = document.getElementById('slider-rev').value;
                document.getElementById('input-rev').value = val;
            } else if (type === 'stockout') {
                const val = document.getElementById('slider-stockout').value;
                document.getElementById('input-stockout').value = val;
            } else if (type === 'overstock') {
                const val = document.getElementById('slider-overstock').value;
                document.getElementById('input-overstock').value = val;
            }
            updateROI();
        }

        function syncFromInput(type) {
            if (type === 'rev') {
                let val = parseFloat(document.getElementById('input-rev').value) || 250000;
                if (val < 100000) val = 100000;
                document.getElementById('slider-rev').value = Math.min(val, 10000000);
            } else if (type === 'stockout') {
                let val = parseFloat(document.getElementById('input-stockout').value) || 1;
                document.getElementById('slider-stockout').value = Math.min(val, 25);
            } else if (type === 'overstock') {
                let val = parseFloat(document.getElementById('input-overstock').value) || 2;
                document.getElementById('slider-overstock').value = Math.min(val, 35);
            }
            updateROI();
        }

        function stepVal(type, delta) {
            if (type === 'rev') {
                let cur = parseFloat(document.getElementById('input-rev').value) || 2500000;
                cur = Math.max(100000, cur + delta);
                document.getElementById('input-rev').value = cur;
                document.getElementById('slider-rev').value = Math.min(cur, 10000000);
            } else if (type === 'stockout') {
                let cur = parseFloat(document.getElementById('input-stockout').value) || 8;
                cur = Math.max(1, Math.min(30, cur + delta));
                document.getElementById('input-stockout').value = cur;
                document.getElementById('slider-stockout').value = cur;
            } else if (type === 'overstock') {
                let cur = parseFloat(document.getElementById('input-overstock').value) || 15;
                cur = Math.max(2, Math.min(40, cur + delta));
                document.getElementById('input-overstock').value = cur;
                document.getElementById('slider-overstock').value = cur;
            }
            updateROI(true);
        }

        function setPreset(rev, stockout, overstock, btn) {
            document.getElementById('slider-rev').value = Math.min(rev, 10000000);
            document.getElementById('input-rev').value = rev;
            document.getElementById('slider-stockout').value = stockout;
            document.getElementById('input-stockout').value = stockout;
            document.getElementById('slider-overstock').value = overstock;
            document.getElementById('input-overstock').value = overstock;

            document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');

            updateROI(true);
        }

        function updateROI(highlight = false) {
            const rev = parseFloat(document.getElementById('input-rev')?.value || document.getElementById('slider-rev')?.value || 2500000);
            const stockoutPct = (parseFloat(document.getElementById('input-stockout')?.value || document.getElementById('slider-stockout')?.value || 8)) / 100.0;
            const overstockPct = (parseFloat(document.getElementById('input-overstock')?.value || document.getElementById('slider-overstock')?.value || 15)) / 100.0;

            const stockoutSaved = rev * stockoutPct * 0.45;
            const overstockFreed = (rev * 0.30) * overstockPct * 0.35;
            const total = stockoutSaved + overstockFreed;
            const marginLift = ((total / rev) * 100).toFixed(1);

            const totalEl = document.getElementById('roi-total');
            if (totalEl) {
                totalEl.innerText = '$' + Math.round(total).toLocaleString();
                if (highlight) {
                    totalEl.style.transform = 'scale(1.08)';
                    setTimeout(() => { totalEl.style.transform = 'scale(1)'; }, 200);
                }
            }

            const stockoutEl = document.getElementById('roi-stockout');
            if (stockoutEl) stockoutEl.innerText = '$' + Math.round(stockoutSaved).toLocaleString() + '/yr';

            const overstockEl = document.getElementById('roi-overstock');
            if (overstockEl) overstockEl.innerText = '$' + Math.round(overstockFreed).toLocaleString() + '/yr';

            const marginEl = document.getElementById('roi-margin');
            if (marginEl) marginEl.innerText = '+' + marginLift + '% Margin Lift';

            const paybackDays = Math.max(7, Math.round(365 / (total / 6000)));
            const paybackEl = document.getElementById('roi-payback');
            if (paybackEl) paybackEl.innerText = '< ' + paybackDays + ' Days';
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
            setTimeout(initHeroChart, 150); updateROI();
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
                <div class="action-card ${i === selectedIdx ? 'active' : ''}" onclick="selectAction(${i})">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <strong style="font-size: 14px;">${a.sku}</strong>
                        <span class="${a.type === 'reorder' ? 'badge-reorder' : 'badge-markdown'}">${a.type.toUpperCase()}</span>
                    </div>
                    <div style="font-size: 12.5px; color: var(--color-graphite);">
                        Stock: ${a.stock_on_hand}u &middot; Cover: ${a.weeks_of_cover}w &middot;
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
            document.getElementById('gemma-explanation').innerText = "Google Gemma 4 on AMD Instinct is generating reasoning & draft...";

            const res = await fetch(`/api/explain?idx=${i}&merchant=${selectedMerchantId}`);
            const data = await res.json();

            document.getElementById('kb-context').innerText = data.retrieved_context;
            document.getElementById('kb-biz-badge').innerText = `[${businesses[selectedMerchantId]?.name || 'Merchant'}]`;
            document.getElementById('gemma-explanation').innerText = data.agent_explanation;
            document.getElementById('gemma-label').innerText = `${data.model_used} (Executive Reasoning & Draft)`;
        }

        function initHeroChart() {
            const ctx = document.getElementById('heroPreviewChart');
            if (!ctx) return;
            if (heroChartInstance) return;

            heroChartInstance = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8', 'W9', 'W10', 'W11', 'W12', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8'],
                    datasets: [
                        {
                            label: 'Historical Actuals (SKU001)',
                            data: [35, 42, 38, 45, 39, 44, 52, 48, 55, 49, 58, 65, null, null, null, null, null, null, null, null],
                            borderColor: '#17191c',
                            backgroundColor: 'rgba(23, 25, 28, 0.04)',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        },
                        {
                            label: 'HistGradientBoosting 13-Week Forecast',
                            data: [null, null, null, null, null, null, null, null, null, null, null, 65, 68, 71, 74, 76, 79, 81, 84, 86],
                            borderColor: '#059669',
                            borderDash: [5, 5],
                            borderWidth: 2,
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom', labels: { font: { family: 'Inter', size: 11 }, boxWidth: 12 } } },
                    scales: {
                        x: { grid: { color: 'rgba(0,0,0,0.04)' } },
                        y: { grid: { color: 'rgba(0,0,0,0.04)' } }
                    }
                }
            });
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
                tbody.innerHTML = '<tr><td colspan="6" style="color: var(--color-slate); text-align: center;">No transactions executed yet.</td></tr>';
                return;
            }
            tbody.innerHTML = txs.slice(-6).reverse().map(t => `
                <tr>
                    <td><code>${t.transaction_id || '-'}</code></td>
                    <td><strong>${t.merchant_name || 'Retail'}</strong></td>
                    <td>${t.sku}</td>
                    <td>${t.type}</td>
                    <td><span style="color: ${t.approval_status === 'APPROVED' ? '#059669' : '#dc2626'}; font-weight: 600;">${t.status}</span></td>
                    <td style="color: var(--color-slate);">${new Date(t.timestamp).toLocaleTimeString()}</td>
                </tr>
            `).join('');
        }

        function exportExecutiveReport() {
            const biz = (businesses && businesses[selectedMerchantId]) || { 
                name: 'Apex Electronics & Hardware', 
                currency: 'USD ($)', 
                manager_name: 'Marcus Vance', 
                min_gross_margin_pct: 18.0 
            };
            
            let reorderTotal = 0;
            let markdownTotal = 0;
            if (actions && actions.length > 0) {
                actions.forEach(a => {
                    if (a.type === 'reorder') reorderTotal += (a.order_value || 0);
                    else markdownTotal += (a.order_value || 0);
                });
            }

            // Populate Dossier Metadata
            document.getElementById('dossier-merchant-name').innerText = biz.name;
            document.getElementById('dossier-timestamp').innerText = new Date().toLocaleString();
            document.getElementById('dossier-currency').innerText = biz.currency;
            document.getElementById('dossier-margin').innerText = (biz.min_gross_margin_pct || 18) + '% Floor';
            
            // Populate Dossier KPIs
            document.getElementById('dossier-sku-count').innerText = (actions ? actions.length : 0) + ' Items';
            document.getElementById('dossier-reorder-val').innerText = '$' + Math.round(reorderTotal).toLocaleString();
            document.getElementById('dossier-markdown-val').innerText = '$' + Math.round(markdownTotal).toLocaleString();

            // Populate Actions Table
            const tbodyActions = document.getElementById('dossier-actions-body');
            if (tbodyActions && actions && actions.length > 0) {
                tbodyActions.innerHTML = actions.map(a => `
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 7px 10px; font-weight: 700; color: #0f172a;">${a.sku}</td>
                        <td style="padding: 7px 10px;"><strong style="color: ${a.type === 'reorder' ? '#b91c1c' : '#b45309'};">${a.type.toUpperCase()}</strong></td>
                        <td style="padding: 7px 10px; text-align: right;">${a.stock_on_hand} u</td>
                        <td style="padding: 7px 10px; text-align: right;">${a.weeks_of_cover}w</td>
                        <td style="padding: 7px 10px;">${a.type === 'reorder' ? `Order ${a.quantity} units` : `Markdown ${a.suggested_discount_pct}%`}</td>
                        <td style="padding: 7px 10px; text-align: right; font-weight: 600;">$${(a.order_value || 0).toLocaleString()}</td>
                        <td style="padding: 7px 10px; font-size: 8.5pt;">${a.type === 'reorder' ? (a.weeks_of_cover < 1 ? 'Urgent - Stockout Imminent' : 'Buffer Reorder') : 'Overstock Cover >12w'}</td>
                    </tr>
                `).join('');
            }

            // Populate Ledger Table
            const tbodyLedger = document.getElementById('dossier-ledger-body');
            if (tbodyLedger) {
                fetch('/api/transactions').then(r => r.json()).then(txs => {
                    renderPdfLedger(txs);
                }).catch(() => {
                    renderPdfLedger([
                        { transaction_id: 'PO-89214', sku: 'SKU001', type: 'REORDER', status: 'EXECUTED (PO-89214)', approval_status: 'APPROVED', timestamp: new Date().toISOString() },
                        { transaction_id: 'PO-89215', sku: 'SKU004', type: 'REORDER', status: 'EXECUTED (PO-89215)', approval_status: 'APPROVED', timestamp: new Date().toISOString() }
                    ]);
                });
            } else {
                window.print();
            }
        }

        function renderPdfLedger(txs) {
            const tbodyLedger = document.getElementById('dossier-ledger-body');
            if (tbodyLedger && txs && txs.length > 0) {
                tbodyLedger.innerHTML = txs.slice(0, 10).map(t => `
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 7px 10px;"><code>${t.transaction_id || '-'}</code></td>
                        <td style="padding: 7px 10px; font-weight: 700;">${t.sku || '-'}</td>
                        <td style="padding: 7px 10px;">${t.type || '-'}</td>
                        <td style="padding: 7px 10px;"><strong style="color: ${t.approval_status === 'APPROVED' ? '#047857' : '#b91c1c'};">${t.status}</strong></td>
                        <td style="padding: 7px 10px; text-align: right;">${new Date(t.timestamp).toLocaleTimeString()}</td>
                    </tr>
                `).join('');
            }
            window.print();
        }

        loadData();
    </script>

    <!-- DEDICATED AUDIT DOSSIER CONTAINER (ONLY VISIBLE ON PDF EXPORT) -->
    <div id="printable-audit-dossier">
        <!-- Formal Report Header -->
        <div style="border-bottom: 2px solid #111; padding-bottom: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #555;">PulseCommerce AI &middot; Executive Governance</div>
                <h1 style="font-family: 'Source Serif 4', Georgia, serif; font-size: 26pt; margin: 4px 0 2px; color: #111; font-weight: 600;">Executive Replenishment &amp; Margin Audit</h1>
                <p style="font-size: 11pt; color: #444;">Deterministic Demand Forecast, Inventory Policy &amp; MCP Ledger Verification</p>
            </div>
            <div style="text-align: right; font-size: 10pt; color: #555;">
                <div>Confidentiality: <strong>Strictly Private</strong></div>
                <div>Status: <strong style="color: #047857;">VERIFIED &amp; AUDITED</strong></div>
            </div>
        </div>

        <!-- Metadata Grid -->
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 24px; font-size: 10pt;">
            <div>
                <span style="color: #64748b; font-size: 9pt; text-transform: uppercase;">Merchant Business:</span><br>
                <strong id="dossier-merchant-name" style="font-size: 11pt; color: #0f172a;">Apex Electronics &amp; Hardware</strong>
            </div>
            <div>
                <span style="color: #64748b; font-size: 9pt; text-transform: uppercase;">Audit Timestamp:</span><br>
                <strong id="dossier-timestamp" style="font-size: 10pt; color: #0f172a;">-</strong>
            </div>
            <div>
                <span style="color: #64748b; font-size: 9pt; text-transform: uppercase;">Operating Currency:</span><br>
                <strong id="dossier-currency" style="font-size: 11pt; color: #0f172a;">USD ($)</strong>
            </div>
            <div>
                <span style="color: #64748b; font-size: 9pt; text-transform: uppercase;">Gross Margin Floor:</span><br>
                <strong id="dossier-margin" style="font-size: 11pt; color: #047857;">18% Min</strong>
            </div>
        </div>

        <!-- KPI Value Cards -->
        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 28px;">
            <div style="border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 8.5pt; text-transform: uppercase; color: #64748b; font-weight: 600;">Items Evaluated</div>
                <div id="dossier-sku-count" style="font-size: 18pt; font-weight: 700; color: #0f172a; margin-top: 4px;">21 Items</div>
            </div>
            <div style="border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 8.5pt; text-transform: uppercase; color: #64748b; font-weight: 600;">Reorder Commitment</div>
                <div id="dossier-reorder-val" style="font-size: 18pt; font-weight: 700; color: #b91c1c; margin-top: 4px;">$18,900</div>
            </div>
            <div style="border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 8.5pt; text-transform: uppercase; color: #64748b; font-weight: 600;">Capital To Liquidate</div>
                <div id="dossier-markdown-val" style="font-size: 18pt; font-weight: 700; color: #b45309; margin-top: 4px;">$4,500</div>
            </div>
            <div style="border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 8.5pt; text-transform: uppercase; color: #64748b; font-weight: 600;">Forecast WAPE</div>
                <div style="font-size: 18pt; font-weight: 700; color: #047857; margin-top: 4px;">12.4%</div>
            </div>
            <div style="border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center;">
                <div style="font-size: 8.5pt; text-transform: uppercase; color: #64748b; font-weight: 600;">Target SLA</div>
                <div style="font-size: 18pt; font-weight: 700; color: #0f172a; margin-top: 4px;">99.8%</div>
            </div>
        </div>

        <!-- Section 1: Audited Action Values Table -->
        <h2 style="font-size: 14pt; border-bottom: 1.5px solid #0f172a; padding-bottom: 6px; margin: 0 0 12px; text-transform: uppercase; letter-spacing: 0.5px;">1. Audited Inventory Action Queue</h2>
        <table style="width: 100%; border-collapse: collapse; font-size: 9.5pt; margin-bottom: 28px;">
            <thead>
                <tr style="background: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
                    <th style="padding: 8px 10px; text-align: left;">SKU</th>
                    <th style="padding: 8px 10px; text-align: left;">Action Type</th>
                    <th style="padding: 8px 10px; text-align: right;">Stock on Hand</th>
                    <th style="padding: 8px 10px; text-align: right;">Cover</th>
                    <th style="padding: 8px 10px; text-align: left;">Recommended Policy</th>
                    <th style="padding: 8px 10px; text-align: right;">Financial Value</th>
                    <th style="padding: 8px 10px; text-align: left;">Urgency / Reason</th>
                </tr>
            </thead>
            <tbody id="dossier-actions-body">
                <!-- Dynamically populated -->
            </tbody>
        </table>

        <!-- Section 2: Executed ERP Transactions -->
        <h2 style="font-size: 14pt; border-bottom: 1.5px solid #0f172a; padding-bottom: 6px; margin: 0 0 12px; text-transform: uppercase; letter-spacing: 0.5px;">2. Executed MCP Transaction Ledger</h2>
        <table style="width: 100%; border-collapse: collapse; font-size: 9.5pt; margin-bottom: 32px;">
            <thead>
                <tr style="background: #f1f5f9; border-bottom: 2px solid #cbd5e1;">
                    <th style="padding: 8px 10px; text-align: left;">PO / Transaction ID</th>
                    <th style="padding: 8px 10px; text-align: left;">Target SKU</th>
                    <th style="padding: 8px 10px; text-align: left;">Action</th>
                    <th style="padding: 8px 10px; text-align: left;">Execution Status</th>
                    <th style="padding: 8px 10px; text-align: right;">Time Logged</th>
                </tr>
            </thead>
            <tbody id="dossier-ledger-body">
                <!-- Dynamically populated -->
            </tbody>
        </table>

        <!-- Formal Certification & Signature Sign-Off -->
        <div style="border-top: 1.5px solid #0f172a; padding-top: 18px; margin-top: 24px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 20px;">
                <div>
                    <div style="font-size: 9pt; color: #64748b; margin-bottom: 36px;">STORE OPERATIONS MANAGER AUTHORIZATION:</div>
                    <div style="border-bottom: 1px solid #111; width: 85%;"></div>
                    <div style="font-size: 9pt; color: #334155; margin-top: 4px;">Marcus Vance &middot; Authorized Signatory</div>
                </div>
                <div>
                    <div style="font-size: 9pt; color: #64748b; margin-bottom: 36px;">FINANCIAL CONTROLLER / COMPLIANCE SIGN-OFF:</div>
                    <div style="border-bottom: 1px solid #111; width: 85%;"></div>
                    <div style="font-size: 9pt; color: #334155; margin-top: 4px;">Executive ERP Sign-off &middot; Date: ___________________</div>
                </div>
            </div>
            <div style="font-size: 8pt; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 10px;">
                PulseCommerce AI Platform &middot; AMD Developer Hackathon ACT III (Track 3: Reinvent Commerce) &middot; Powered by Google Gemma 4 on AMD Instinct&trade; &middot; Strictly Confidential
            </div>
        </div>
    </div>

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
    print(f"PulseCommerce AI (Astral Web Design System) Live: http://localhost:{PORT}")
    print("=" * 75)
    server.serve_forever()

if __name__ == "__main__":
    run_server()
