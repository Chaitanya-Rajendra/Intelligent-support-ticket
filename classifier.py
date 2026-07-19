import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open(os.path.join(os.path.dirname(__file__), "..", "prompts", "classification_prompt.txt")) as f:
    SYSTEM_PROMPT = f.read()


def classify_ticket(raw_text: str) -> dict:
    """
    Sends ticket text to the LLM and returns a structured classification:
    intent, priority, confidence, suggested_department, and an optional
    auto-drafted response for low-complexity/high-confidence cases.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Fallback if the model doesn't return clean JSON
        result = {
            "intent": "unclassified",
            "priority": "medium",
            "confidence": 0.0,
            "suggested_department": "general_support",
            "auto_response": None,
        }

    # Basic guardrails on expected fields/values
    result.setdefault("intent", "unclassified")
    result.setdefault("priority", "medium")
    result.setdefault("confidence", 0.0)
    result.setdefault("suggested_department", "general_support")
    result.setdefault("auto_response", None)

    return result
