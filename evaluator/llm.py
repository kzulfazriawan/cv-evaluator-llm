import time
import json
import requests
from decouple import config


class OpenRouterClient:
    """
    Wrapper for OpenRouter Chat API with retry, backoff, and JSON-safe parsing.
    """

    CHAT_URL = 'https://openrouter.ai/api/v1/chat/completions'

    def __init__(self, api_key: str = None, timeout: int = 60):
        self.api_key = api_key or config('OPENROUTER_API_KEY')
        self.session = requests.Session()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.timeout = timeout

    @staticmethod
    def try_parse_json(text: str):
        """
        Try to parse JSON from the text response.
        """
        if not text:
            return None

        # Direct attempt
        try:
            return json.loads(text)
        except Exception: pass

        # Try substring extraction
        start, end = text.find('{'), text.rfind('}') + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except Exception: pass

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
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'response_format': {'type': 'json_object'}
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
                resp.raise_for_status()
                data = resp.json()

                choice = data.get('choices', [{}])[0].get('message', {}).get('content')

                # Already a dict
                if isinstance(choice, dict):
                    return choice

                # Try parse string into JSON
                parsed = OpenRouterClient.try_parse_json(choice)
                if parsed is not None:
                    return parsed

                # Fallback wrapper
                return {'__raw': choice, '__meta': data}

            except Exception as e:
                last_err = e
                if attempt == retries:
                    raise RuntimeError(
                        f'OpenRouter call failed after {retries} attempts: {e}'
                    ) from e
                time.sleep(delay)
                delay *= backoff_factor

        raise RuntimeError('Unexpected failure in OpenRouter call') from last_err
