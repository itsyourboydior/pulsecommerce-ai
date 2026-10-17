"""Main Application: End-to-end Inventory & Promotion Agent Orchestrator.
Flow:
1. Load proposed actions from out/actions.json (derived from ML forecast + inventory rules)
2. Retrieve relevant supplier policies and margin rules from Knowledge Base
3. Invoke Evolus Workflow / Gemma 4 on AMD to generate transparent reasoning and communication drafts
4. Human-in-the-Loop manager evaluation (Approve / Reject)
5. Execute approved decisions via MCP connector directly into ERP / POS mock
6. Save auditable log of executed actions to out/executed_actions.json
"""
import os
import sys
import json
import argparse
from dotenv import load_dotenv

from evolus_client import EvolusClient
from knowledge_base import get_context_for_action
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

def run_pipeline(limit=5, auto_approve=True, manager_name="Store Manager"):
    """Runs the full pipeline for a set of proposed actions."""
    actions = load_actions()
    total_actions = len(actions)
    selected_actions = actions[:limit] if limit else actions
    
    print("=" * 70)
    print("  INVENTORY & PROMOTION AGENT (AMD Instinct + Gemma 4 + Evolus + MCP)")
    print("=" * 70)
    print(f"Total actions loaded: {total_actions} | Processing: {len(selected_actions)}\n")
    
    evolus = EvolusClient()
    executed_results = []
    
    for idx, action in enumerate(selected_actions, 1):
        sku = action.get("sku")
        act_type = action.get("type").upper()
        print("-" * 70)
        print(f"[{idx}/{len(selected_actions)}] SKU: {sku} | Action: {act_type}")
        print(f"  Stock on hand: {action.get('stock_on_hand')} units | Weeks of cover: {action.get('weeks_of_cover')}w")
        
        if act_type == "REORDER":
            print(f"  Proposed Order: {action.get('quantity')} units (Urgency: {action.get('urgency')}, Value: €{action.get('order_value')})")
        else:
            print(f"  Proposed Markdown: {action.get('suggested_discount_pct')}% (Excess: {action.get('excess_units')} units)")
            
        # 1. Retrieve Knowledge
        kb_ctx = get_context_for_action(action)
        print(f"  [Knowledge Library] Matched Supplier: {kb_ctx['supplier']['name']}")
        
        # 2. Run Evolus Workflow / Gemma 4
        print("  [Evolus / Gemma 4] Generating reasoning and draft...")
        wf_res = evolus.run_workflow(action, kb_ctx["retrieved_rules"])
        print(f"  Model Engine: {wf_res.get('model_used', 'Gemma 4')}")
        
        agent_text = wf_res.get("agent_explanation", "")
        # Print indent
        for line in agent_text.splitlines():
            print(f"    {line}")
            
        # 3. Human-in-the-Loop Approval
        # In demo mode, approve all except the last one to show the rejection audit trail
        decision = auto_approve
        if auto_approve and idx == len(selected_actions) and len(selected_actions) > 1:
            decision = False # Intentionally reject one to demonstrate rejection handling
            
        print(f"\n  [Human-in-the-Loop] Manager Decision: {'APPROVED' if decision else 'REJECTED'}")
        
        # 4. MCP Execution
        mcp_res = InventoryMCPService.execute_action(
            action=action,
            approved=decision,
            approved_by=manager_name,
            supplier_info=kb_ctx["supplier"]
        )
        
        if mcp_res.get("success"):
            print(f"  [MCP Execution] SUCCESS -> {mcp_res.get('message')}")
        else:
            print(f"  [MCP Execution] NOT EXECUTED -> {mcp_res.get('message')}")
            
        record = {
            "action": action,
            "knowledge_context": kb_ctx["retrieved_rules"],
            "workflow_result": wf_res,
            "manager_decision": "APPROVED" if decision else "REJECTED",
            "manager_name": manager_name,
            "mcp_execution": mcp_res
        }
        executed_results.append(record)
        print()
        
    # Save executed actions log
    with open(EXECUTED_PATH, "w", encoding="utf-8") as f:
        json.dump(executed_results, f, indent=2)
        
    print("=" * 70)
    print(f"Pipeline completed successfully! {len(executed_results)} actions processed.")
    print(f"Audit log saved to: {EXECUTED_PATH}")
    print("=" * 70)
    return executed_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Inventory & Promotion Agent")
    parser.add_argument("--limit", type=int, default=3, help="Number of actions to process (default: 3)")
    parser.add_argument("--auto-approve", action="store_true", default=True, help="Auto-approve for batch/demo")
    args = parser.parse_args()
    
    run_pipeline(limit=args.limit, auto_approve=args.auto_approve)
