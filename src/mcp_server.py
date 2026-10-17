"""MCP (Model Context Protocol) Inventory Connector & Execution Engine.
Simulates a multi-merchant ERP / WMS / Point-of-Sale System.
Records executed purchase orders and promotional markdowns only after Store Manager approval.
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
                              order_value: float, approval_status: str, approved_by: str = "Store Manager",
                              merchant_id: str = "apex_electronics", merchant_name: str = "Apex Electronics"):
        """Tool: create_purchase_order
        Places an auditable purchase order in the merchant's ERP/Inventory system.
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
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
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
            "message": f"Successfully created Purchase Order {po_id} for {quantity} units of {sku} [{merchant_name}].",
            "transaction": tx
        }

    @staticmethod
    def apply_markdown(sku: str, discount_pct: float, excess_units: int, 
                       approval_status: str, approved_by: str = "Store Manager",
                       merchant_id: str = "lumina_fashion", merchant_name: str = "Lumina Fashion"):
        """Tool: apply_markdown
        Applies a promotional markdown discount to an overstocked SKU in the POS pricing catalog.
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
            "merchant_id": merchant_id,
            "merchant_name": merchant_name,
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
            "message": f"Successfully updated POS catalog: {discount_pct}% discount applied to {sku} [{merchant_name}].",
            "transaction": tx
        }

    @staticmethod
    def execute_action(action: dict, approved: bool, approved_by: str = "Store Manager", business_info: dict = None):
        """Unified executor called by Evolus / Orchestrator when human decision is made."""
        approval_status = "APPROVED" if approved else "REJECTED"
        act_type = action.get("type")
        sku = action.get("sku")
        
        m_id = business_info.get("id", "apex_electronics") if business_info else "apex_electronics"
        m_name = business_info.get("name", "Store Merchant") if business_info else "Retail Merchant"
        
        if not approved:
            return {
                "success": False,
                "sku": sku,
                "merchant_name": m_name,
                "action_type": act_type,
                "status": "REJECTED_BY_MANAGER",
                "message": f"Action for {sku} was rejected by {approved_by} [{m_name}]."
            }
            
        sup_name = "Approved Vendor"
        if business_info and business_info.get("suppliers"):
            sup_name = business_info["suppliers"][0].get("name", "Approved Vendor")
        
        if act_type == "reorder":
            return InventoryMCPService.create_purchase_order(
                sku=sku,
                quantity=action.get("quantity", 0),
                supplier=sup_name,
                urgency=action.get("urgency", "normal"),
                order_value=action.get("order_value", 0.0),
                approval_status=approval_status,
                approved_by=approved_by,
                merchant_id=m_id,
                merchant_name=m_name
            )
        elif act_type == "markdown":
            return InventoryMCPService.apply_markdown(
                sku=sku,
                discount_pct=action.get("suggested_discount_pct", 15),
                excess_units=action.get("excess_units", 0),
                approval_status=approval_status,
                approved_by=approved_by,
                merchant_id=m_id,
                merchant_name=m_name
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
    biz = {"id": "apex_electronics", "name": "Apex Electronics"}
    res = InventoryMCPService.execute_action(test_action, approved=True, business_info=biz)
    print(json.dumps(res, indent=2))
