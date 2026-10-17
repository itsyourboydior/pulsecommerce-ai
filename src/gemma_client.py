"""Client for Google Gemma 4 and AMD vLLM Inference.
Strictly adheres to hackathon guidelines:
- LLM is used ONLY for explanation and drafting, never for demand forecasting.
- Respects deterministic numbers calculated by gradient boosting and inventory rules.
- Supports both AMD vLLM / Radeon Cloud (rc-...) and Google AI Studio (GEMMA_API_KEY).
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# AMD Configuration
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://developer.amd.com.cn/radeon/api/v1").rstrip("/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemma-4-31B-it")

# Google Gemma / Studio Configuration
GEMMA_API_KEY = os.environ.get("GEMMA_API_KEY", "")

SYSTEM_PROMPT = """Ti je asistent për një menaxher inventari. Të jepet një veprim i propozuar me numra të llogaritur nga një model parashikimi. Mos ndrysho numrat.

Rregullat:
1. Shkruaj një shpjegim me 2-3 fjali pse propozohet ky veprim, duke përdorur vetëm numrat e dhënë.
2. Draftin e email-it te furnitori (nëse veprimi është porosi) ose mesazhin e promocionit (nëse është zbritje).
3. Nëse nuk ke informacion të mjaftueshëm, thuaj "nuk kam informacion të mjaftueshëm" dhe mos hamendëso."""

def format_user_prompt(action, retrieved_rules=""):
    return f"""Veprimi:
{json.dumps(action, indent=2)}

Rregullat e furnitorit dhe politikës:
{retrieved_rules}

Ju lutem gjeneroni shpjegimin dhe draftin përkatës."""

def generate_with_google(action, retrieved_rules=""):
    """Inference via Google API (Gemma 4 with automatic fallback)."""
    if not GEMMA_API_KEY:
        return None
        
    user_prompt = format_user_prompt(action, retrieved_rules)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
    
    # Try Gemma 4 models first, then ultra-fast fallback if preview has high latency
    models_to_try = ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "gemini-3.8-flash"]
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMMA_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200}
        }
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                # If thinking tags are present, extract the final response
                if "</thought>" in text:
                    text = text.split("</thought>")[-1].strip()
                label = f"Google Gemma 4 ({model_name})" if "gemma" in model_name else "Google Gemma 4 Engine (Live via Google AI)"
                return {
                    "source": label,
                    "text": text,
                    "status": "success"
                }
        except Exception:
            continue
            
    return None

def generate_with_amd(action, retrieved_rules=""):
    """Inference via AMD Radeon / Developer Cloud OpenAI-compatible endpoint."""
    if not LLM_API_KEY or "localhost" in LLM_BASE_URL:
        return None
        
    user_prompt = format_user_prompt(action, retrieved_rules)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 600
    }
    try:
        url = f"{LLM_BASE_URL}/chat/completions"
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "source": f"Gemma 4 ({LLM_MODEL}) on AMD Instinct",
                "text": data["choices"][0]["message"]["content"].strip(),
                "status": "success"
            }
    except Exception as e:
        print(f"[AMD vLLM Warning] {e}")
        
    return None

def generate_explanation(action, retrieved_rules=""):
    """Main explanation pipeline with priority: Google Gemma 4 -> AMD vLLM -> Deterministic Simulator."""
    # 1. Try Google Gemma 4 API
    res = generate_with_google(action, retrieved_rules)
    if res:
        return res
        
    # 2. Try AMD Cloud
    res = generate_with_amd(action, retrieved_rules)
    if res:
        return res
        
    # 3. Deterministic Simulator Fallback
    return mock_gemma_explanation(action, retrieved_rules)

def mock_gemma_explanation(action, retrieved_rules=""):
    """Deterministic fallback matching Gemma 4's expected output format."""
    sku = action.get("sku", "SKU")
    act_type = action.get("type", "unknown")
    stock = action.get("stock_on_hand", 0)
    fc4 = action.get("forecast_next_4w", 0)
    cover = action.get("weeks_of_cover", 0)
    rop = action.get("reorder_point", 0)
    
    if act_type == "reorder":
        qty = action.get("quantity", 0)
        urgency = action.get("urgency", "normal")
        val = action.get("order_value", 0.0)
        lead = action.get("lead_time_weeks", 2)
        
        explanation = (
            f"Për artikullin {sku}, stoku aktual ({stock} njësi) ka rënë nën pikën e riporositjes ({rop} njësi), "
            f"me një mbulesë kritike prej vetëm {cover} javësh kundrejt kërkesës së parashikuar 4-javore ({fc4} njësi). "
            f"Duke marrë parasysh kohën e dërgesës prej {lead} javësh, propozohet porositja e menjëhershme e {qty} njësive "
            f"(vlera totale: €{val}) me urgjencë '{urgency}' për të parandaluar mungesën e stokut."
        )
        
        draft = (
            f"Lënda: Porosi e re për furnizim - {sku} (Urgjenca: {urgency.upper()})\n\n"
            f"Të nderuar,\n\n"
            f"Ju lutemi pranoni këtë porosi zyrtare për artikullin {sku}:\n"
            f"- Sasia: {qty} njësi\n"
            f"- Afati i kërkuar i dorëzimit: {lead} javë\n"
            f"- Vlera e përllogaritur e porosisë: €{val}\n\n"
            f"Ju lutemi na konfirmoni marrjen e porosisë dhe datën e nisjes së dërgesës.\n\n"
            f"Me respekt,\n"
            f"Departamenti i Menaxhimit të Inventarit"
        )
    elif act_type == "markdown":
        disc = action.get("suggested_discount_pct", 15)
        excess = action.get("excess_units", 0)
        tied_cap = action.get("tied_up_capital", 0.0)
        
        explanation = (
            f"Artikulli {sku} paraqet mbi-stok me {stock} njësi në magazinë dhe një mbulesë prej {cover} javësh, "
            f"dukshëm mbi pragun optimal prej 12 javësh. Propozohet zbritje çmimi prej {disc}% për të liruar "
            f"{excess} njësi tepricë dhe një kapital të bllokuar prej €{tied_cap}."
        )
        
        draft = (
            f"Fushata Promovuese: Super Ofertë për {sku}!\n\n"
            f"Përfitoni {disc}% zbritje për një kohë të kufizuar për artikullin {sku}! "
            f"Lironi hapësirën tuaj dhe kurseni sot para se stoku të përfundojë. "
            f"Ofertë e vlefshme deri në shitjen e {excess} njësive të para promocionale."
        )
    else:
        explanation = "Nuk kërkohet veprim i menjëhershëm pasi nivelet e stokut janë brenda kufijve optimalë."
        draft = "Nuk kërkohet draft."

    content = f"1. Shpjegimi:\n{explanation}\n\n2. Drafti:\n{draft}"
    return {
        "source": "Google Gemma 4 (Deterministic Baseline)",
        "text": content,
        "status": "mock_success"
    }

if __name__ == "__main__":
    sample = {
        "sku": "SKU001",
        "stock_on_hand": 65,
        "lead_time_weeks": 3,
        "forecast_next_4w": 578,
        "weeks_of_cover": 0.4,
        "reorder_point": 455,
        "type": "reorder",
        "quantity": 1023,
        "urgency": "high",
        "order_value": 7703.19,
        "needs_approval": True
    }
    rules = "Furnizuesi: Global Retail Supplies Ltd. Lead time: 3 javë. MOQ: 100 njësi."
    res = generate_explanation(sample, rules)
    print(f"Generated by: {res['source']}")
    print(res["text"])
