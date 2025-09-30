# evaluator/llm.py
import time
import json
import requests
from decouple import config


class OpenRouterClient:
    """
    Wrapper for OpenRouter Chat API with retry, backoff, and JSON-safe parsing.
    Handles 429 (rate limit) errors gracefully.
    """

    CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str = None, timeout: int = 60):
        self.api_key = api_key or config("OPENROUTER_API_KEY")
        self.session = requests.Session()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = timeout

    def _try_parse_json(self, text: str):
        """Try to parse JSON from the text response."""
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            pass
        start, end = text.find("{"), text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception:
                pass
        return None

    def chat(self, model: str, messages: list,
             temperature: float = 0.2,
             max_tokens: int = 1200,
             retries: int = 3,
             backoff_factor: int = 2):
        """
        Call OpenRouter chat completions API.
        Ensures a dict response (parsed JSON or fallback wrapper).
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }

        delay = 1
        last_err = None

        for attempt in range(1, retries + 1):
            try:
                resp = self.session.post(
                    self.CHAT_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )

                # --- Handle 429 Too Many Requests ---
                if resp.status_code == 429:
                    if attempt == retries:
                        return {"error": "Rate limited by provider. Please retry later.", "code": 429}
                    time.sleep(delay * 5)  # longer backoff for rate limit
                    delay *= backoff_factor
                    continue

                resp.raise_for_status()
                data = resp.json()

                choice = data.get("choices", [{}])[0].get("message", {}).get("content")

                if isinstance(choice, dict):
                    return choice

                parsed = self._try_parse_json(choice)
                if parsed is not None:
                    return parsed

                return {"__raw": choice, "__meta": data}

            except Exception as e:
                last_err = e
                if attempt == retries:
                    raise RuntimeError(
                        f"OpenRouter call failed after {retries} attempts: {e}"
                    ) from e
                time.sleep(delay)
                delay *= backoff_factor

        raise RuntimeError("Unexpected failure in OpenRouter call") from last_err
