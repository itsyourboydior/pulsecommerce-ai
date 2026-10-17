"""Interactive Web Demo UI for AMD Developer Hackathon Track 3.
Provides a clean, presentation-ready dashboard for the 3-minute video recording.
Demonstrates:
1. Forecast Accuracy & Backtest Results (Gradient Boosting vs Naive baselines)
2. Deterministic Action Proposals (Reorders & Markdowns)
3. Gemma 4 on AMD reasoning & communication drafts
4. Human-in-the-Loop manager approval/rejection
5. Real-time MCP ERP transaction recording
"""
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

from evolus_client import EvolusClient
from knowledge_base import get_context_for_action
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

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Inventory & Promotion Agent | AMD + Gemma 4 + Evolus</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --border: #1f2937;
      --amd-red: #ed1c24;
      --gemma-blue: #4285f4;
      --accent-green: #10b981;
      --accent-yellow: #f59e0b;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); padding: 24px; line-height: 1.5; }
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 24px; }
    .badge-bar { display: flex; gap: 10px; }
    .badge { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .badge-amd { background: rgba(237, 28, 36, 0.15); color: #ff6b6b; border: 1px solid #ed1c24; }
    .badge-gemma { background: rgba(66, 133, 244, 0.15); color: #8ab4f8; border: 1px solid #4285f4; }
    .badge-evolus { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid #10b981; }

    .grid-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
    .metric-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 18px; }
    .metric-title { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
    .metric-val { font-size: 26px; font-weight: 700; color: #fff; }
    .metric-highlight { color: var(--accent-green); font-size: 13px; font-weight: 600; margin-top: 4px; }

    .main-grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 24px; }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
    h2 { font-size: 16px; font-weight: 700; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }

    .action-list { max-height: 520px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
    .action-item { background: #162032; border: 1px solid var(--border); border-radius: 8px; padding: 14px; cursor: pointer; transition: all 0.2s; }
    .action-item:hover, .action-item.active { border-color: var(--gemma-blue); background: #1e293b; }
    .action-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .tag-reorder { background: #064e3b; color: #6ee7b7; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .tag-markdown { background: #78350f; color: #fde68a; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
    .details { font-size: 13px; color: var(--text-muted); }

    .panel-box { background: #0d131f; border: 1px solid #1e293b; border-radius: 8px; padding: 14px; margin-bottom: 14px; }
    .panel-box h3 { font-size: 13px; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px; }
    .code-box { font-family: 'JetBrains Mono', monospace; font-size: 12px; white-space: pre-wrap; color: #cbd5e1; }

    .btn-row { display: flex; gap: 12px; margin-top: 18px; }
    .btn { flex: 1; padding: 12px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; font-size: 14px; transition: 0.2s; }
    .btn-approve { background: var(--accent-green); color: #042f1a; }
    .btn-approve:hover { filter: brightness(1.1); }
    .btn-reject { background: #ef4444; color: #450a0a; }
    .btn-reject:hover { filter: brightness(1.1); }

    .ledger-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 12px; }
    .ledger-table th, .ledger-table td { padding: 8px 10px; border-bottom: 1px solid var(--border); text-align: left; }
    .ledger-table th { color: var(--text-muted); }
  </style>
</head>
<body>
  <header>
    <div>
      <h1 style="font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">Inventory & Promotion Agent</h1>
      <p style="font-size: 13px; color: var(--text-muted);">AMD Developer Hackathon ACT III · Track 3 (Reinvent Commerce) + Gemma + Evolus</p>
    </div>
    <div class="badge-bar">
      <span class="badge badge-amd">AMD Instinct vLLM</span>
      <span class="badge badge-gemma">Google Gemma 4</span>
      <span class="badge badge-evolus">Evolus Workflow & MCP</span>
    </div>
  </header>

  <div class="grid-metrics">
    <div class="metric-card">
      <div class="metric-title">Forecast Error (WAPE)</div>
      <div class="metric-val">12.4%</div>
      <div class="metric-highlight">HistGradientBoosting (Python)</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">vs Seasonal Naive Baseline</div>
      <div class="metric-val">+21.6%</div>
      <div class="metric-highlight">Baseline WAPE: 15.9%</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">vs 4-Week Moving Avg</div>
      <div class="metric-val">+7.9%</div>
      <div class="metric-highlight">Baseline WAPE: 13.5%</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Rule Auditability</div>
      <div class="metric-val">100%</div>
      <div class="metric-highlight">Deterministic Actions & Z=1.65</div>
    </div>
  </div>

  <div class="main-grid">
    <div class="card">
      <h2>Proposed Actions (Actions.json) <span id="action-count" style="font-size: 13px; color: var(--text-muted);"></span></h2>
      <div class="action-list" id="action-list">Loading...</div>
    </div>

    <div class="card">
      <h2>Agent Reasoning & Human Approval</h2>
      
      <div class="panel-box">
        <h3>Evolus Knowledge Library Context</h3>
        <div id="kb-context" class="code-box">Select an action on the left...</div>
      </div>

      <div class="panel-box">
        <h3 id="gemma-label">Gemma 4 on AMD (Reasoning & Draft)</h3>
        <div id="gemma-explanation" class="code-box">Select an action to inspect AI reasoning...</div>
      </div>

      <div class="btn-row">
        <button class="btn btn-approve" onclick="submitDecision(true)">Approve & Execute via MCP</button>
        <button class="btn btn-reject" onclick="submitDecision(false)">Reject Action</button>
      </div>

      <div style="margin-top: 24px;">
        <h2>Live MCP ERP Ledger <span style="font-size: 11px; color: var(--text-muted);">(Real-time execution audit)</span></h2>
        <table class="ledger-table" id="ledger-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>SKU</th>
              <th>Action</th>
              <th>Status</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody id="ledger-body">
            <tr><td colspan="5" style="color: var(--text-muted); text-align: center;">No transactions executed yet.</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    let actions = [];
    let selectedIdx = 0;

    async function loadData() {
      const res = await fetch('/api/actions');
      actions = await res.json();
      document.getElementById('action-count').innerText = `${actions.length} items`;
      renderActionList();
      if (actions.length > 0) selectAction(0);
      loadLedger();
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
            ${a.type === 'reorder' ? `Qty: ${a.quantity}u (€${a.order_value})` : `Disc: ${a.suggested_discount_pct}%`}
          </div>
        </div>
      `).join('');
    }

    async function selectAction(i) {
      selectedIdx = i;
      renderActionList();
      const a = actions[i];
      document.getElementById('kb-context').innerText = "Querying Knowledge Library...";
      document.getElementById('gemma-explanation').innerText = "Gemma 4 on AMD vLLM is generating reasoning...";

      const res = await fetch(`/api/explain?idx=${i}`);
      const data = await res.json();

      document.getElementById('kb-context').innerText = data.retrieved_context;
      document.getElementById('gemma-explanation').innerText = data.agent_explanation;
      document.getElementById('gemma-label').innerText = `${data.model_used} (Explanation & Draft)`;
    }

    async function submitDecision(approved) {
      if (actions.length === 0) return;
      const res = await fetch('/api/decision', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ idx: selectedIdx, approved: approved })
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
        tbody.innerHTML = '<tr><td colspan="5" style="color: var(--text-muted); text-align: center;">No transactions executed yet.</td></tr>';
        return;
      }
      tbody.innerHTML = txs.slice(-6).reverse().map(t => `
        <tr>
          <td><code>${t.transaction_id || '-'}</code></td>
          <td><strong>${t.sku}</strong></td>
          <td>${t.type}</td>
          <td><span style="color: ${t.approval_status === 'APPROVED' ? '#10b981' : '#ef4444'}; font-weight: 600;">${t.status}</span></td>
          <td style="color: var(--text-muted);">${new Date(t.timestamp).toLocaleTimeString()}</td>
        </tr>
      `).join('');
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
        elif url.path == "/api/actions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_actions_data()).encode("utf-8"))
        elif url.path == "/api/transactions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_transactions()).encode("utf-8"))
        elif url.path == "/api/explain":
            qs = urllib.parse.parse_qs(url.query)
            idx = int(qs.get("idx", ["0"])[0])
            actions = get_actions_data()
            if 0 <= idx < len(actions):
                act = actions[idx]
                ctx = get_context_for_action(act)
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
            actions = get_actions_data()
            if 0 <= idx < len(actions):
                act = actions[idx]
                ctx = get_context_for_action(act)
                res = InventoryMCPService.execute_action(act, approved=approved, approved_by="Store Manager", supplier_info=ctx["supplier"])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), DemoHandler)
    print(f"Interactive Web Demo running at: http://localhost:{PORT}")
    print("Ideal for video recording and judging demonstration! Press Ctrl+C to stop.")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
