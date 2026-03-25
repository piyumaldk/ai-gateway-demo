import re
import random
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests
import urllib3

from config import (
    APIM_GATEWAY_URL,
    APIM_GATEWAY_AUTH_MODE,
    APIM_GATEWAY_TOKEN,
    APIM_VERIFY_SSL,
)

if not APIM_VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class ChatResponse:
    success: bool
    content: str
    blocked: bool = False
    guardrail_type: str = ""
    tokens_used: int = 0
    latency_ms: int = 0
    status_code: int = 0
    raw_response: Optional[Dict] = None


class GatewayClient:
    """Sends chat requests through the APIM gateway to different guardrail APIs."""

    def __init__(self):
        self.gateway_url = APIM_GATEWAY_URL
        self.verify_ssl = APIM_VERIFY_SSL

        self.session = requests.Session()
        if APIM_GATEWAY_AUTH_MODE == "apikey":
            self.session.headers.update({
                "Internal-Key": APIM_GATEWAY_TOKEN,
                "Content-Type": "application/json",
            })
        else:
            self.session.headers.update({
                "Authorization": f"Bearer {APIM_GATEWAY_TOKEN}",
                "Content-Type": "application/json",
            })

    def send_chat(self, message: str, context: str, version: str,
                  chat_path: str, model: str) -> ChatResponse:
        start = time.time()
        url = self._build_url(context, version, chat_path)
        payload = {"model": model, "messages": [{"role": "user", "content": message}]}

        try:
            resp = self.session.post(url, json=payload, verify=self.verify_ssl, timeout=30)
            latency = int((time.time() - start) * 1000)

            # Guardrail blocked (HTTP 446)
            if resp.status_code == 446:
                data = self._safe_json(resp)
                # Extract guardrail details from the response
                guardrail_type = "UNKNOWN"
                assessments = ""
                message_data = data.get("message", "")
                if isinstance(message_data, dict):
                    guardrail_type = message_data.get("interveningGuardrail", "UNKNOWN")
                    assessments = message_data.get("assessments", "")
                    action_reason = message_data.get("actionReason", "Guardrail policy violation detected.")
                    direction = message_data.get("direction", "REQUEST")
                    content = (
                        f"**Guardrail:** {guardrail_type}\n\n"
                        f"**Reason:** {action_reason}\n\n"
                        f"**Direction:** {direction}"
                    )
                    if assessments:
                        content += f"\n\n**Assessment:** {assessments}"
                elif isinstance(message_data, str):
                    content = message_data
                    # Try to extract guardrail name from description
                    desc = data.get("description", "")
                    if "Violation of" in desc:
                        guardrail_type = desc.replace("Violation of ", "").replace(" detected.", "")
                    content = f"**Blocked:** {desc}" if desc else content
                else:
                    content = str(data)

                return ChatResponse(
                    success=True, blocked=True, status_code=446, latency_ms=latency,
                    content=content, guardrail_type=guardrail_type, raw_response=data,
                )

            # Success
            if resp.status_code == 200:
                data = self._safe_json(resp)
                return ChatResponse(
                    success=True, status_code=200, latency_ms=latency,
                    content=data["choices"][0]["message"]["content"],
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                    raw_response=data,
                )

            # Errors
            return ChatResponse(
                success=False, status_code=resp.status_code, latency_ms=latency,
                content=f"Gateway returned {resp.status_code}: {resp.text[:300]}\n\nURL: {url}",
            )

        except requests.exceptions.ConnectionError:
            return ChatResponse(success=False, latency_ms=int((time.time() - start) * 1000),
                content=f"Cannot connect to gateway at {self.gateway_url}. Is APIM running?")
        except requests.exceptions.Timeout:
            return ChatResponse(success=False, content="Request timed out (30s).")
        except Exception as e:
            return ChatResponse(success=False, content=f"Error: {e}")

    def _build_url(self, context: str, version: str, chat_path: str) -> str:
        ctx = "/" + context.strip("/")
        ver = version.strip("/")
        path = "/" + chat_path.strip("/")
        if ver and ctx.rstrip("/").endswith(f"/{ver}"):
            base = f"{self.gateway_url}{ctx}{path}"
        elif ver:
            base = f"{self.gateway_url}{ctx}/{ver}{path}"
        else:
            base = f"{self.gateway_url}{ctx}{path}"
        # Azure OpenAI needs ?api-version= for date-style versions
        if ver and re.match(r"^\d{4}-\d{2}-\d{2}$", ver):
            base += f"?api-version={ver}"
        return base

    def test_connection(self) -> bool:
        try:
            resp = self.session.get(
                f"{self.gateway_url}/health", verify=self.verify_ssl, timeout=5)
            return resp.status_code < 500
        except Exception:
            return False

    @staticmethod
    def _safe_json(resp) -> dict:
        try:
            return resp.json()
        except Exception:
            return {}
