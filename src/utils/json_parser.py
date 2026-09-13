import json
import re
from src.utils.exceptions import JSONParseError

def parse_llm_json(text: str) -> dict:
    """
    Safely parses JSON from LLM response strings, stripping markdown fences if present.
    """
    if not text or not isinstance(text, str):
        raise JSONParseError("Empty or invalid LLM output text")

    cleaned = text.strip()

    # Match JSON block inside ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    else:
        # Fallback: look for the first '{' and last '}'
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and start < end:
            cleaned = cleaned[start:end+1].strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
        raise JSONParseError("Parsed JSON is not an object/dictionary")
    except Exception as e:
        raise JSONParseError(f"Failed to parse JSON from LLM output: {str(e)}")
