"""Evolus API Client & Workflow Orchestrator.
Uses Evolus's official API protocol:
- Base URL: https://api.evolus.ai/v1
- Endpoint: /chat/completions
- Authentication: Bearer <EVOLUS_API_KEY>
- Model Format: {applicationId}:{agentId}
"""
import os
import json
import requests
from dotenv import load_dotenv

from knowledge_base import get_context_for_action
from gemma_client import generate_explanation, SYSTEM_PROMPT, format_user_prompt

load_dotenv()

EVOLUS_BASE_URL = os.environ.get("EVOLUS_BASE_URL", "https://api.evolus.ai/v1").rstrip("/")
EVOLUS_API_KEY = os.environ.get("EVOLUS_API_KEY", "")
EVOLUS_MODEL_ID = os.environ.get("EVOLUS_MODEL_ID", "")  # Expected format: {applicationId}:{agentId}

class EvolusClient:
    def __init__(self, base_url=None, api_key=None, model_id=None):
        self.base_url = (base_url or EVOLUS_BASE_URL).rstrip("/")
        self.api_key = api_key or EVOLUS_API_KEY
        self.model_id = model_id or EVOLUS_MODEL_ID

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def run_agent(self, action: dict, retrieved_context: str = None):
        """Triggers the Evolus Agent via https://api.evolus.ai/v1/chat/completions.
        Model format required by Evolus: {applicationId}:{agentId}
        """
        if not retrieved_context:
            ctx_data = get_context_for_action(action)
            retrieved_context = ctx_data["retrieved_rules"]

        user_content = format_user_prompt(action, retrieved_context)

        # If live model ID ({applicationId}:{agentId}) is configured, call Evolus API
        if self.api_key and self.model_id and ":" in self.model_id:
            try:
                url = f"{self.base_url}/chat/completions"
                payload = {
                    "model": self.model_id,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    "temperature": 0.2
                }
                resp = requests.post(url, json=payload, headers=self.get_headers(), timeout=45)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "source": f"Evolus Cloud Agent ({self.model_id})",
                        "status": "success",
                        "agent_explanation": content,
                        "raw_response": data,
                        "needs_approval": action.get("needs_approval", True)
                    }
                else:
                    print(f"[EvolusClient Warning] Evolus API returned {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[EvolusClient Warning] Failed connecting to Evolus Cloud: {e}")

        # Fallback / Local simulation mode
        explanation_res = generate_explanation(action, retrieved_context)
        return {
            "source": "Evolus Agent Simulator (Awaiting {applicationId}:{agentId})",
            "status": "workflow_executed",
            "workflow_id": self.model_id or "pending_agent_id",
            "input_action": action,
            "retrieved_context": retrieved_context,
            "agent_explanation": explanation_res["text"],
            "model_used": explanation_res["source"],
            "needs_approval": action.get("needs_approval", True)
        }

    # Backward compatibility
    def run_workflow(self, action: dict, retrieved_context: str = None):
        return self.run_agent(action, retrieved_context)

if __name__ == "__main__":
    client = EvolusClient()
    sample = {
        "sku": "SKU001",
        "type": "reorder",
        "stock_on_hand": 65,
        "lead_time_weeks": 3,
        "forecast_next_4w": 578,
        "weeks_of_cover": 0.4,
        "reorder_point": 455,
        "quantity": 1023,
        "urgency": "high",
        "order_value": 7703.19,
        "needs_approval": True
    }
    res = client.run_agent(sample)
    print("Agent Result:")
    print(json.dumps(res, indent=2))
