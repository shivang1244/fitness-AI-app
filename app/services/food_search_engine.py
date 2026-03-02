import json
from typing import Dict, Any


class FoodSearchEngine:

    def search_food(
        self,
        food_name: str,
        grams: float,
        gpt_client
    ) -> Dict[str, Any]:

        if not isinstance(food_name, str):
            raise ValueError("Food name must be a string")

        prompt = self.build_prompt(food_name, grams)

        response = gpt_client(prompt)

        return self.safe_json_parse(response)

    # =====================================================
    # GPT PROMPT
    # =====================================================
    def build_prompt(self, food_name: str, grams: float) -> str:

        return f"""
You are a professional nutrition information assistant.

Provide nutritional breakdown for:

Food: {food_name}
Quantity: {grams} grams

Return STRICT JSON:

{{
  "food_name": "{food_name}",
  "grams": {grams},
  "calories": 0,
  "protein": 0,
  "carbs": 0,
  "fat": 0,
  "fiber": 0,
  "micronutrients": [
    {{
      "name": "",
      "amount": ""
    }}
  ]
}}
"""

    # =====================================================
    # SAFE JSON PARSER (UPDATED)
    # =====================================================
    def safe_json_parse(self, response):

        # If LLMClient already returned dict → return directly
        if isinstance(response, dict):
            return response

        # If not string → invalid
        if not isinstance(response, str):
            raise ValueError("Invalid GPT response type")

        try:
            return json.loads(response)
        except Exception:
            cleaned = response.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "")
                cleaned = cleaned.replace("```", "").strip()

            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start != -1 and end != -1:
                cleaned = cleaned[start:end + 1]

            return json.loads(cleaned)