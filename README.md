# Inventory & Promotion Agent (AMD Instinct + Google Gemma 4 + Evolus + MCP)

> **AMD Developer Hackathon ACT III · Track 3 (Reinvent Commerce)**  
> *Google (Gemma) Prize Track & Evolus Prize Track Submission*

An autonomous, transparent retail operations agent that empowers small and medium merchants to prevent stockouts and eliminate overstocked dead capital.

---

## 1. System Architecture & Core Flow

The system strictly adheres to the Track 3 commerce rules: **classical statistical machine learning is used for deterministic demand forecasting**, while **Gemma 4 on AMD Instinct GPUs is used for agentic reasoning, supplier negotiations, and promotional drafting**.

```
   [ Weekly Sales Data ]
             │
             ▼
   [ HistGradientBoosting ]  ───► Demand Forecast (Horizon = 13 weeks)
             │
             ▼
   [ Inventory Policy Engine ] ───► Deterministic Action Proposals (Reorders & Markdowns)
             │                      (Safety stock Z=1.65, Overstock cover > 12w)
             ▼
   [ Evolus Workflow Orchestrator ]
        ├── 1. Knowledge Library (Supplier MOQ, Lead Times, Margin Limits)
        ├── 2. Gemma 4 on AMD Instinct (vLLM OpenAI-Compatible API)
        │       └── Produces transparent reasoning + Vendor PO draft / Markdown copy
        ├── 3. Human-in-the-Loop Gate (Store Manager Approval / Rejection)
        └── 4. MCP Connector (Model Context Protocol ERP/WMS execution)
             │
             ▼
   [ Audited ERP / POS Ledger ] ───► Purchase Orders Created / Pricing Updated
```

---

## 2. Verified Benchmark Results (Backtest)

Evaluated via a **rolling-origin backtest** across 4 evaluation windows (weeks 104, 116, 128, 140) on retail SKU demand:

| Model / Approach | WAPE (Weighted Absolute Percentage Error) | Relative Improvement |
| :--- | :---: | :---: |
| **Seasonal Naive Baseline** (same week last year) | 15.9% | Baseline |
| **Moving Average Baseline** (4-week rolling mean) | 13.5% | +15.1% |
| **Our HistGradientBoosting Model (Python)** | **12.4%** | **+7.9% vs Best Baseline** (+21.6% vs Naive) |

> **Note on Data**: Numbers above were calculated using the reproducible backtesting harness (`src/backtest.py`). When benchmarking on real public datasets (such as Kaggle M5 Forecasting or UCI Online Retail II), execute `python src/load_real_data.py --csv <path>` followed by `python src/backtest.py`.

---

## 3. Technology Stack & Deliverables

* **Compute & Acceleration**: AMD Developer Cloud / ROCm running on AMD Instinct GPUs (MI300X / tokenfactory).
* **Language Model**: **Google Gemma 4** (`google/gemma-4-31B-it`, or `26B-A4B`, `E4B`) hosted via vLLM.
* **Agentic Orchestration**: **Evolus Cloud** (`app.evolus.ai`) leveraging 5 core building blocks:
  1. *Custom Model Endpoint* (AMD vLLM integration).
  2. *Knowledge Library* (`knowledge/supplier_rules.md`).
  3. *Multi-step Workflow* (Ingest -> Contextualize -> Reason -> Approve -> Execute).
  4. *Human-in-the-Loop* (Audited manager approvals).
  5. *MCP Connector* (Inventory execution).
* **Machine Learning & Core**: Python 3.11+, Scikit-Learn, Pandas, NumPy.
* **Containerization**: Docker & Docker Compose.

---

## 4. Project Structure

```
inventory-agent/
├── data/
│   ├── sales.csv              # Historical weekly sales (SKU, week, units, price, promo)
│   └── inventory.csv          # Stock on hand, unit cost, lead times
├── knowledge/
│   ├── supplier_rules.json    # Structured vendor conditions, MOQs, margin boundaries
│   └── supplier_rules.md      # Ready for direct upload to Evolus Knowledge Library
├── out/
│   ├── actions.json           # Rule-generated proposed actions
│   ├── backtest_results.json  # Backtest error metrics (WAPE)
│   ├── executed_actions.json  # Full workflow results with Gemma explanations
│   └── mcp_transactions.json  # Auditable ERP/POS ledger from MCP execution
├── src/
│   ├── synth_retail.py        # Retail data simulator
│   ├── forecast.py           # HistGradientBoosting demand forecasting model
│   ├── backtest.py           # Rolling-origin evaluation engine
│   ├── actions.py            # Inventory policy engine (reorder / markdown)
│   ├── knowledge_base.py     # Local retriever for vendor policies
│   ├── gemma_client.py       # AMD vLLM client for Google Gemma 4
│   ├── evolus_client.py      # Evolus API client & workflow bridge
│   ├── mcp_server.py         # MCP ERP tool server & transaction ledger
│   ├── load_real_data.py     # Aggregator for UCI Online Retail / M5 datasets
│   ├── app.py                # End-to-end CLI pipeline orchestrator
│   └── web_demo.py           # Interactive UI for demo video recording
├── .env.example              # Template for API credentials (AMD & Evolus)
├── .gitignore                # Excludes secrets, keys, and virtual environments
├── Dockerfile                # Production container specification
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 5. Quick Start & Execution

### 1. Local Environment Setup
```bash
git clone https://github.com/your-username/inventory-agent.git
cd inventory-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

### 2. Run Demand Forecast & Action Engine
```bash
cd src
# 1. Generate weekly sales & inventory
python synth_retail.py

# 2. Run backtest benchmark against baselines
python backtest.py

# 3. Generate proposed reorders and markdowns
python actions.py
```

### 3. Run the Full Agent Pipeline (Gemma + Evolus + MCP)
```bash
# Run end-to-end pipeline
python app.py --limit 3
```

### 4. Launch the Interactive Web Dashboard (For Video Demo)
```bash
python web_demo.py
```
Open **`http://localhost:8080`** in your browser. You will see:
- Live backtest metrics & WAPE benchmark cards.
- Proposed actions list with stock cover & urgency.
- Real-time Gemma 4 reasoning and supplier email/promotion drafts.
- **Approve / Reject** buttons triggering MCP ERP execution.
- Real-time MCP transaction ledger.

---

## 6. Docker Deployment

Build and run in an isolated container:

```bash
# Build the container
docker build -t inventory-agent .

# Run the pipeline
docker run --rm --env-file .env inventory-agent

# Run the interactive web demo on port 8080
docker run --rm -p 8080:8080 --env-file .env inventory-agent python src/web_demo.py
```

---

## 7. Connecting AMD Developer Cloud & Evolus

### A. Deploying Gemma 4 on AMD Instinct (vLLM)
If deploying your own ROCm container on an AMD instance:
```bash
docker pull vllm/vllm-openai-rocm:latest

vllm serve google/gemma-4-31B-it \
  --max-model-len 32768 \
  --port 8000
```
Test the connection via curl:
```bash
curl http://YOUR-AMD-IP:8000/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-4-31B-it","messages":[{"role":"user","content":"Say hello"}]}'
```

### B. Configuring Evolus Workspace
1. **Custom Model**: In your Evolus workspace, add a custom OpenAI-compatible endpoint with your AMD vLLM URL and model name `google/gemma-4-31B-it`.
2. **Knowledge Library**: Upload `knowledge/supplier_rules.md`.
3. **Workflow**: Set up input parameters matching `out/actions.json` format, link the Gemma 4 node with the prompt from `src/gemma_client.py`, and link the MCP connector.

---

## 8. 3-Minute Video Demo Script

1. **The Problem (0:00 - 0:20)**: Retailers lose revenue from stockouts and lock cash in dead inventory.
2. **Deterministic Forecasting (0:20 - 1:00)**: Show `out/backtest_results.json` and explain why Track 3 rules forbid raw LLM forecasting. Highlight the **12.4% WAPE (7.9% improvement)**.
3. **Action Generation (1:00 - 1:30)**: Show `actions.json`—how mathematical safety stock ($Z=1.65$) flags reorders and cover $>12$ weeks flags markdowns.
4. **Gemma 4 on AMD (1:30 - 2:10)**: Show Gemma 4 reasoning on the dashboard, explaining *why* the order is needed using exact numbers and drafting the vendor email according to supplier terms.
5. **Human-in-the-Loop & MCP (2:10 - 2:40)**: Demonstrate manager approval of an urgent PO and rejection of an unnecessary order. Show the MCP ledger recording the transaction.
6. **Summary & Value (2:40 - 3:00)**: Conclude on how this architecture bridges auditable machine learning, high-performance AMD hardware, and agentic governance.

---

## 9. Security & Ethics
* **Strict Credential Protection**: No API keys or credentials are hardcoded or tracked in Git.
* **Bounded Hallucinations**: Gemma 4 is explicitly prompted never to alter deterministic mathematical outputs from the forecasting model.
* **Mandatory Governance**: Critical financial transactions are non-autonomous and require explicit manager sign-off.
