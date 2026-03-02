import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


class LLMClient:

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openai/gpt-4o-mini"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set.")

    def generate(self, prompt: str, temperature: float = 0.4):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Fitness App"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a JSON-only AI engine. "
                        "Return strictly valid raw JSON. "
                        "Do not add explanations. "
                        "Do not use markdown. "
                        "Do not wrap JSON in backticks."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=90
        )

        if response.status_code != 200:
            raise Exception(f"OpenRouter Error: {response.text}")

        data = response.json()

        # 🔥 Validate structure safely
        if "choices" not in data:
            raise Exception(f"Unexpected OpenRouter response: {data}")

        content = data["choices"][0]["message"]["content"]

        return self._force_json_dict(content)

    # =====================================================
    # 🔥 HARD JSON NORMALIZER
    # =====================================================
    def _force_json_dict(self, content):

        # Already dict
        if isinstance(content, dict):
            return content

        if not isinstance(content, str):
            raise Exception("Model returned unsupported response type")

        cleaned = content.strip()

        # Remove markdown if present
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "")
            cleaned = cleaned.replace("```", "").strip()

        # Extract JSON block if model added text
        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            cleaned = cleaned[start:end + 1]

        try:
            parsed = json.loads(cleaned)
        except Exception:
            print("----- RAW MODEL OUTPUT -----")
            print(content)
            raise Exception("Model did not return valid JSON")

        if not isinstance(parsed, dict):
            raise Exception("Model JSON is not an object")

        return parsed