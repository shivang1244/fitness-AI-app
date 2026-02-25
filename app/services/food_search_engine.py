import json
from typing import Dict, Any


class FoodSearchEngine:

    def search_food(
        self,
        food_name: str,
        grams: float,
        gpt_client
    ) -> Dict[str, Any]:

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

Requirements:
- Provide realistic nutritional values.
- Be accurate and practical.
- Educational tone only.
- No explanations outside JSON.
- Do NOT add extra commentary.

Return STRICT JSON format:

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
    # SAFE JSON PARSER
    # =====================================================
    def safe_json_parse(self, response: str):

        try:
            return json.loads(response)
        except Exception:
            cleaned = response.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            return json.loads(cleaned[start:end])
