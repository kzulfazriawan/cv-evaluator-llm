# evaluator/llm_openrouter.py
import time, json, requests
from decouple import config

OPENROUTER_KEY = config("OPENROUTER_API_KEY")
CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}

def call_openrouter_chat(model: str, messages: list, temperature: float = 0.2,
                         max_tokens: int = 1200, retries: int = 3):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }
    backoff = 1
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(CHAT_URL, headers=HEADERS, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            # response content path: choices[0].message.content
            choice = data.get("choices", [{}])[0].get("message", {}).get("content")
            # If already dict
            if isinstance(choice, dict):
                return choice
            # If string, try parse JSON
            try:
                return json.loads(choice)
            except Exception:
                # try to locate a JSON substring
                txt = choice or ""
                start = txt.find("{")
                end = txt.rfind("}") + 1
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(txt[start:end])
                    except Exception:
                        pass
                # final fallback: return wrapper
                return {"__raw": txt, "__meta": data}
        except Exception as e:
            last_err = e
            if attempt == retries:
                raise
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError("OpenRouter failed") from last_err
