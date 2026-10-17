"""Multi-tenant Knowledge Base: loads merchant policies and supplier SLAs
to provide context to Gemma 4 and Evolus workflows.
Supports distinct business profiles (Electronics, Fashion, Specialty Food).
"""
import json
import os

BUSINESS_FILE = os.path.join(os.path.dirname(__file__), "..", "knowledge", "businesses.json")

def load_businesses():
    if os.path.exists(BUSINESS_FILE):
        with open(BUSINESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("businesses", {})
    return {}

def get_business_by_id(business_id="apex_electronics"):
    bizs = load_businesses()
    return bizs.get(business_id) or list(bizs.values())[0]

def get_context_for_action(action, business_id=None):
    """Retrieves relevant business profile, supplier SLA, and pricing rules for a given action."""
    bizs = load_businesses()
    sku = action.get("sku", "")
    action_type = action.get("type", "")
    
    # Identify business by ID or by SKU coverage
    selected_biz = None
    if business_id and business_id in bizs:
        selected_biz = bizs[business_id]
    else:
        for b_id, b_data in bizs.items():
            for sup in b_data.get("suppliers", []):
                if sku in sup.get("skus", []):
                    selected_biz = b_data
                    break
            if selected_biz:
                break
                
    if not selected_biz:
        selected_biz = list(bizs.values())[0] if bizs else {
            "name": "Standard Enterprise Retail",
            "currency": "USD ($)",
            "min_gross_margin_pct": 20.0,
            "max_discount_pct": 25.0,
            "suppliers": []
        }

    # Find matched supplier within the business
    matched_supplier = None
    for sup in selected_biz.get("suppliers", []):
        if sku in sup.get("skus", []):
            matched_supplier = sup
            break
            
    if not matched_supplier:
        matched_supplier = {
            "name": "Primary Approved Vendor Ltd",
            "lead_time_weeks": action.get("lead_time_weeks", 2),
            "moq_units": 50,
            "payment_terms": "Net 30",
            "contact_email": "orders@approved-vendor.example.com"
        }

    curr = selected_biz.get("currency", "USD ($)")
    min_margin = selected_biz.get("min_gross_margin_pct", 18.0)
    max_disc = selected_biz.get("max_discount_pct", 25.0)

    if action_type == "reorder":
        rules_text = (
            f"Merchant: {selected_biz['name']} (Currency: {curr}). "
            f"Supplier: {matched_supplier['name']} ({matched_supplier.get('contact_email', 'orders@vendor.com')}). "
            f"Lead Time: {matched_supplier.get('lead_time_weeks', 2)} weeks. "
            f"Minimum Order Quantity (MOQ): {matched_supplier.get('moq_units', 50)} units. "
            f"Payment Terms: {matched_supplier.get('payment_terms', 'Net 30')}."
        )
    elif action_type == "markdown":
        rules_text = (
            f"Merchant: {selected_biz['name']} (Currency: {curr}). "
            f"Inventory Overstock Threshold: 12 weeks of cover. "
            f"Margin Protection Rule: Minimum gross margin guaranteed at {min_margin}%. "
            f"Promotional Policy: Maximum allowable discount capped at {max_disc}%."
        )
    else:
        rules_text = f"Merchant: {selected_biz['name']} (Currency: {curr}). Standard inventory policies apply."

    return {
        "business": selected_biz,
        "supplier": matched_supplier,
        "currency": curr,
        "retrieved_rules": rules_text
    }

if __name__ == "__main__":
    test_action = {"sku": "SKU001", "type": "reorder", "quantity": 1023, "lead_time_weeks": 3}
    ctx = get_context_for_action(test_action)
    print("Multi-tenant Context Example:")
    print(ctx["retrieved_rules"])
