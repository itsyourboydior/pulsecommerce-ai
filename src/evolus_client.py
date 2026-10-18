"""Evolus API Client & Workflow Orchestrator.
Uses Evolus's official REST API protocol:
- Base URL: https://api.evolus.ai/api/v1
- Authentication: X-ApiKey + X-Application-Id headers
- AI Tools: POST /api/v1/ai-tools/{tool}/run
- Also supports OpenAI-compatible agent chat endpoint
"""
import os
import json
import requests
from dotenv import load_dotenv

from knowledge_base import get_context_for_action
from gemma_client import generate_explanation, SYSTEM_PROMPT, format_user_prompt

load_dotenv()

EVOLUS_BASE_URL = os.environ.get("EVOLUS_BASE_URL", "https://api.evolus.ai/api/v1").rstrip("/")
EVOLUS_API_KEY = os.environ.get("EVOLUS_API_KEY", "")
EVOLUS_MODEL_ID = os.environ.get("EVOLUS_MODEL_ID", "")  # workflow or agent ID

class EvolusClient:
    def __init__(self, base_url=None, api_key=None, model_id=None):
        self.base_url = (base_url or EVOLUS_BASE_URL).rstrip("/")
        self.api_key = api_key or EVOLUS_API_KEY
        self.model_id = model_id or EVOLUS_MODEL_ID

    def get_headers(self):
        """Evolus REST API requires X-ApiKey and X-Application-Id."""
        headers = {
            "X-ApiKey": self.api_key,
            "Content-Type": "application/json"
        }
        # If model_id has applicationId:agentId format, extract app ID
        if self.model_id and ":" in self.model_id:
            app_id = self.model_id.split(":")[0]
            headers["X-Application-Id"] = app_id
        elif self.model_id:
            headers["X-Application-Id"] = self.model_id
        return headers

    def run_agent(self, action: dict, retrieved_context: str = None):
        """Triggers the Evolus Agent workflow via REST API.
        Tries multiple endpoints: ai-tools/run, then chat/completions (OpenAI-compat).
        """
        if not retrieved_context:
            ctx_data = get_context_for_action(action)
            retrieved_context = ctx_data["retrieved_rules"]

        user_content = format_user_prompt(action, retrieved_context)

        if self.api_key and self.model_id:
            # Attempt 1: Evolus AI Tools endpoint
            result = self._try_ai_tools(action, user_content)
            if result:
                return result

            # Attempt 2: OpenAI-compatible chat/completions
            result = self._try_chat_completions(user_content, action)
            if result:
                return result

            # Attempt 3: Evolus agent chat via Bearer auth (legacy)
            result = self._try_bearer_chat(user_content, action)
            if result:
                return result

        # Fallback: Local simulation using Gemma client
        explanation_res = generate_explanation(action, retrieved_context)
        return {
            "source": f"Evolus Agent (Local Mode → {explanation_res['source']})",
            "status": "workflow_executed",
            "workflow_id": self.model_id or "local_simulation",
            "input_action": action,
            "retrieved_context": retrieved_context,
            "agent_explanation": explanation_res["text"],
            "model_used": explanation_res["source"],
            "needs_approval": action.get("needs_approval", True)
        }

    def _try_ai_tools(self, action, user_content):
        """POST /api/v1/ai-tools/{tool}/run"""
        try:
            tool_id = self.model_id.split(":")[-1] if ":" in self.model_id else self.model_id
            url = f"{self.base_url}/ai-tools/{tool_id}/run"
            payload = {
                "input": user_content,
                "context": {
                    "action": action,
                    "system_prompt": SYSTEM_PROMPT
                }
            }
            resp = requests.post(url, json=payload, headers=self.get_headers(), timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("output", data.get("result", data.get("text", json.dumps(data))))
                return {
                    "source": f"Evolus Cloud AI Tool ({self.model_id})",
                    "status": "success",
                    "agent_explanation": content if isinstance(content, str) else json.dumps(content),
                    "raw_response": data,
                    "needs_approval": action.get("needs_approval", True)
                }
            else:
                print(f"[Evolus AI-Tools] {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[Evolus AI-Tools] {e}")
        return None

    def _try_chat_completions(self, user_content, action):
        """OpenAI-compatible chat endpoint with X-ApiKey auth."""
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
                print(f"[Evolus Chat] {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[Evolus Chat] {e}")
        return None

    def _try_bearer_chat(self, user_content, action):
        """Legacy Bearer auth attempt for Evolus chat completions."""
        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_id,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.2
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "source": f"Evolus Cloud (Bearer Auth) ({self.model_id})",
                    "status": "success",
                    "agent_explanation": content,
                    "raw_response": data,
                    "needs_approval": action.get("needs_approval", True)
                }
            else:
                print(f"[Evolus Bearer] {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[Evolus Bearer] {e}")
        return None

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
    print(json.dumps(res, indent=2, ensure_ascii=False))

