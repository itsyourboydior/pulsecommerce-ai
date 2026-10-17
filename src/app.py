"""Main Application: Multi-Tenant Inventory & Promotion Agent Orchestrator (100% English).
Flow:
1. Load proposed actions from out/actions.json (derived from ML forecast + inventory rules)
2. Retrieve merchant profile, supplier policies, and margin rules from Knowledge Base
3. Invoke Evolus Workflow / Google Gemma 4 on AMD to generate executive reasoning and drafts
4. Human-in-the-Loop manager evaluation (Approve / Reject)
5. Execute approved decisions via MCP connector directly into ERP / POS system
6. Save auditable log of executed actions to out/executed_actions.json
"""
import os
import sys
import json
import argparse
from dotenv import load_dotenv

from evolus_client import EvolusClient
from knowledge_base import get_context_for_action, load_businesses
from mcp_server import InventoryMCPService

load_dotenv()

ACTIONS_PATH = os.path.join(os.path.dirname(__file__), "..", "out", "actions.json")
EXECUTED_PATH = os.path.join(os.path.dirname(__file__), "..", "out", "executed_actions.json")

def load_actions():
    if not os.path.exists(ACTIONS_PATH):
        print("[App] out/actions.json not found! Running actions.py first...")
        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "actions.py")], check=True)
        
    with open(ACTIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_pipeline(limit=3, auto_approve=True, business_id=None):
    """Runs the full pipeline for a set of proposed actions under a chosen business profile."""
    actions = load_actions()
    total_actions = len(actions)
    selected_actions = actions[:limit] if limit else actions
    
    print("=" * 75)
    print("  RETAIL COMMERCE AGENT (AMD Instinct + Google Gemma 4 + Evolus + MCP)")
    print("=" * 75)
    print(f"Total actions loaded: {total_actions} | Processing queue: {len(selected_actions)}\n")
    
    evolus = EvolusClient()
    executed_results = []
    
    for idx, action in enumerate(selected_actions, 1):
        sku = action.get("sku")
        act_type = action.get("type").upper()
        
        # 1. Retrieve Knowledge for Merchant
        kb_ctx = get_context_for_action(action, business_id=business_id)
        biz = kb_ctx["business"]
        sup = kb_ctx["supplier"]
        curr = kb_ctx["currency"]
        
        print("-" * 75)
        print(f"[{idx}/{len(selected_actions)}] Merchant: {biz['name']} | SKU: {sku} | Action: {act_type}")
        print(f"  Stock on hand: {action.get('stock_on_hand')} units | Current Cover: {action.get('weeks_of_cover')} weeks")
        
        if act_type == "REORDER":
            print(f"  Proposed Order: {action.get('quantity')} units (Urgency: {action.get('urgency').upper()}, Value: ${action.get('order_value')})")
        else:
            print(f"  Proposed Markdown: {action.get('suggested_discount_pct')}% (Excess: {action.get('excess_units')} units)")
            
        print(f"  [Knowledge Library] Supplier: {sup['name']} | Terms: {sup.get('payment_terms', 'Net 30')}")
        
        # 2. Run Evolus Workflow / Gemma 4
        print("  [Evolus / Gemma 4] Synthesizing executive reasoning & communication draft...")
        wf_res = evolus.run_workflow(action, kb_ctx["retrieved_rules"])
        print(f"  Model Engine: {wf_res.get('model_used', 'Gemma 4')}")
        
        agent_text = wf_res.get("agent_explanation", "")
        for line in agent_text.splitlines():
            print(f"    {line}")
            
        # 3. Human-in-the-Loop Approval
        # In automated demonstration, approve all except one to demonstrate audit trail
        decision = auto_approve
        if auto_approve and idx == len(selected_actions) and len(selected_actions) > 1:
            decision = False
            
        manager = biz.get("manager_name", "Store Manager")
        print(f"\n  [Human-in-the-Loop Governance] Store Manager ({manager}): {'APPROVED' if decision else 'REJECTED'}")
        
        # 4. MCP Execution
        mcp_res = InventoryMCPService.execute_action(
            action=action,
            approved=decision,
            approved_by=manager,
            business_info=biz
        )
        
        if mcp_res.get("success"):
            print(f"  [MCP ERP Execution] SUCCESS -> {mcp_res.get('message')}")
        else:
            print(f"  [MCP ERP Execution] NOT EXECUTED -> {mcp_res.get('message')}")
            
        record = {
            "merchant": biz,
            "action": action,
            "knowledge_context": kb_ctx["retrieved_rules"],
            "workflow_result": wf_res,
            "manager_decision": "APPROVED" if decision else "REJECTED",
            "manager_name": manager,
            "mcp_execution": mcp_res
        }
        executed_results.append(record)
        print()
        
    with open(EXECUTED_PATH, "w", encoding="utf-8") as f:
        json.dump(executed_results, f, indent=2)
        
    print("=" * 75)
    print(f"Pipeline completed successfully! {len(executed_results)} decisions audited.")
    print(f"Audit log saved to: {EXECUTED_PATH}")
    print("=" * 75)
    return executed_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Multi-Tenant Inventory & Promotion Agent")
    parser.add_argument("--limit", type=int, default=3, help="Number of actions to process (default: 3)")
    parser.add_argument("--auto-approve", action="store_true", default=True, help="Auto-approve for demo")
    parser.add_argument("--merchant", type=str, default="apex_electronics", help="Merchant profile ID")
    args = parser.parse_args()
    
    run_pipeline(limit=args.limit, auto_approve=args.auto_approve, business_id=args.merchant)
