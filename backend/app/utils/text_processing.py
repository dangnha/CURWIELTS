import json
import re
from typing import Any


def json_loads(text: str) -> dict[str, Any]:
    """Safely parse JSON from an LLM response.

    Models are instructed to reply with JSON only, but real-world output
    sometimes wraps it in a markdown code fence and/or adds a sentence of
    preamble/trailing commentary despite the instruction — especially on
    providers without a strict JSON response mode. Try, in order:
    1. Parse as-is (fast path for well-behaved responses).
    2. Strip a ``` / ```json fence, wherever it appears in the text.
    3. Extract the first balanced top-level {...} block from the raw text.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    # Nothing worked — raise the original, most informative parse error.
    return json.loads(text)
