"""MCP (Model Context Protocol) Inventory Connector & Mock Execution Engine.
Simulates a real ERP / WMS / Inventory Management System.
Records executed purchase orders and markdown changes only after Human-in-the-Loop manager approval.
"""
import os
import json
import uuid
from datetime import datetime, timezone

TRANSACTIONS_LOG = os.path.join(os.path.dirname(__file__), "..", "out", "mcp_transactions.json")

def ensure_ledger():
    os.makedirs(os.path.dirname(TRANSACTIONS_LOG), exist_ok=True)
    if not os.path.exists(TRANSACTIONS_LOG):
        with open(TRANSACTIONS_LOG, "w", encoding="utf-8") as f:
            json.dump([], f)

def get_transactions():
    ensure_ledger()
    with open(TRANSACTIONS_LOG, "r", encoding="utf-8") as f:
        return json.load(f)

def record_transaction(tx):
    ensure_ledger()
    txs = get_transactions()
    txs.append(tx)
    with open(TRANSACTIONS_LOG, "w", encoding="utf-8") as f:
        json.dump(txs, f, indent=2)

class InventoryMCPService:
    """MCP Tools exposed for inventory execution."""
    
    @staticmethod
    def create_purchase_order(sku: str, quantity: int, supplier: str, urgency: str, 
                              order_value: float, approval_status: str, approved_by: str = "Store Manager"):
        """Tool: create_purchase_order
        Places an auditable purchase order in the ERP/Inventory system.
        Requires approval_status == 'APPROVED'.
        """
        if approval_status.upper() != "APPROVED":
            return {
                "success": False,
                "error": "Human approval required! Purchase order was REJECTED or PENDING.",
                "sku": sku
            }
            
        po_id = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        tx = {
            "transaction_id": po_id,
            "type": "PURCHASE_ORDER",
            "sku": sku,
            "quantity": quantity,
            "supplier": supplier,
            "urgency": urgency,
            "order_value": order_value,
            "approval_status": approval_status,
            "approved_by": approved_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "EXECUTED_IN_ERP"
        }
        record_transaction(tx)
        return {
            "success": True,
            "po_number": po_id,
            "message": f"Successfully created Purchase Order {po_id} for {quantity} units of {sku}.",
            "transaction": tx
        }

    @staticmethod
    def apply_markdown(sku: str, discount_pct: float, excess_units: int, 
                       approval_status: str, approved_by: str = "Store Manager"):
        """Tool: apply_markdown
        Applies a promotional markdown discount to an overstocked SKU in the pricing catalog.
        Requires approval_status == 'APPROVED'.
        """
        if approval_status.upper() != "APPROVED":
            return {
                "success": False,
                "error": "Human approval required! Markdown promotion was REJECTED or PENDING.",
                "sku": sku
            }
            
        promo_id = f"PR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        tx = {
            "transaction_id": promo_id,
            "type": "MARKDOWN_PROMOTION",
            "sku": sku,
            "discount_pct": discount_pct,
            "excess_units_cleared": excess_units,
            "approval_status": approval_status,
            "approved_by": approved_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "APPLIED_IN_POS_CATALOG"
        }
        record_transaction(tx)
        return {
            "success": True,
            "promo_id": promo_id,
            "message": f"Successfully updated POS catalog: {discount_pct}% discount applied to {sku}.",
            "transaction": tx
        }

    @staticmethod
    def execute_action(action: dict, approved: bool, approved_by: str = "Store Manager", supplier_info: dict = None):
        """Unified executor called by Evolus / Orchestrator when human decision is made."""
        approval_status = "APPROVED" if approved else "REJECTED"
        act_type = action.get("type")
        sku = action.get("sku")
        
        if not approved:
            return {
                "success": False,
                "sku": sku,
                "action_type": act_type,
                "status": "REJECTED_BY_MANAGER",
                "message": f"Action for {sku} was rejected by {approved_by}."
            }
            
        sup_name = supplier_info.get("name", "Default Vendor") if supplier_info else "Approved Supplier"
        
        if act_type == "reorder":
            return InventoryMCPService.create_purchase_order(
                sku=sku,
                quantity=action.get("quantity", 0),
                supplier=sup_name,
                urgency=action.get("urgency", "normal"),
                order_value=action.get("order_value", 0.0),
                approval_status=approval_status,
                approved_by=approved_by
            )
        elif act_type == "markdown":
            return InventoryMCPService.apply_markdown(
                sku=sku,
                discount_pct=action.get("suggested_discount_pct", 15),
                excess_units=action.get("excess_units", 0),
                approval_status=approval_status,
                approved_by=approved_by
            )
        else:
            return {"success": False, "error": f"Unknown action type: {act_type}"}

if __name__ == "__main__":
    test_action = {
        "sku": "SKU001",
        "type": "reorder",
        "quantity": 1023,
        "urgency": "high",
        "order_value": 7703.19
    }
    print("Testing MCP Reorder Execution with Manager Approval:")
    res = InventoryMCPService.execute_action(test_action, approved=True, approved_by="Store Manager")
    print(json.dumps(res, indent=2))
