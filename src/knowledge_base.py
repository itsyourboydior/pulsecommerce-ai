"""Knowledge Base retriever: loads supplier policies and margin rules
to provide context to Gemma 4 (AMD vLLM) and Evolus workflow."""
import json
import os

KNOWLEDGE_FILE = os.path.join(os.path.dirname(__file__), "..", "knowledge", "supplier_rules.json")

def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"suppliers": {}, "pricing_rules": {}}

def get_context_for_action(action):
    """Retrieves relevant supplier information and pricing policies for a given action dictionary."""
    kb = load_knowledge()
    sku = action.get("sku", "")
    action_type = action.get("type", "")
    
    # Match supplier
    matched_supplier = None
    for sup_id, sup_info in kb.get("suppliers", {}).items():
        if sku in sup_info.get("skus_covered", []):
            matched_supplier = {"id": sup_id, **sup_info}
            break
            
    if not matched_supplier:
        matched_supplier = {
            "name": "Standard Approved Vendor",
            "lead_time_weeks": action.get("lead_time_weeks", 2),
            "moq_units": 50,
            "payment_terms": "Net 30",
            "contact_email": "purchasing@vendor-hub.example.com"
        }
        
    pricing_rules = kb.get("pricing_rules", {})
    
    if action_type == "reorder":
        rules_text = (
            f"Furnizuesi: {matched_supplier['name']} ({matched_supplier['contact_email']}). "
            f"Koha e dërgesës (lead time): {matched_supplier['lead_time_weeks']} javë. "
            f"Sasia minimale e porosisë (MOQ): {matched_supplier.get('moq_units', 50)} njësi. "
            f"Kushtet e pagesës: {matched_supplier.get('payment_terms', 'Net 30')}."
        )
    elif action_type == "markdown":
        rules_text = (
            f"Rregullat e zbritjes: Pragu i mbi-stokut është {pricing_rules.get('markdown_triggers', {}).get('overstock_weeks_threshold', 12)} javë. "
            f"Margjina minimale e garantuar: {pricing_rules.get('minimum_gross_margin_pct', 18)}%. "
            f"Zbritja maksimale e lejuar: {pricing_rules.get('maximum_discount_pct', 30)}%."
        )
    else:
        rules_text = "Nuk ka rregulla shtesë të specifikuara për këtë veprim."
        
    return {
        "supplier": matched_supplier,
        "pricing_rules": pricing_rules,
        "retrieved_rules": rules_text
    }

if __name__ == "__main__":
    sample_action = {"sku": "SKU001", "type": "reorder", "quantity": 1023, "lead_time_weeks": 3}
    ctx = get_context_for_action(sample_action)
    print("Retrieved context:")
    print(ctx["retrieved_rules"])
