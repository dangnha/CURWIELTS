import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class FetchModelsRequest(BaseModel):
    provider: str = "gemini"
    api_key: str


@router.post("/fetch-models")
async def fetch_available_models(data: FetchModelsRequest):
    """Fetch available models from the provider using the user's API key."""
    if data.provider != "gemini":
        return {"models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"] if data.provider == "chatgpt" else DEFAULT_MODELS_LISTS.get(data.provider, ["auto"])}

    if not data.api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    try:
        import google.generativeai as genai
        genai.configure(api_key=data.api_key)
        models = genai.list_models()
        gemini_models = []
        for m in models:
            name = m.name.replace("models/", "")
            if "generateContent" in m.supported_generation_methods:
                gemini_models.append({
                    "name": name,
                    "display_name": m.display_name,
                    "description": m.description[:100] if m.description else "",
                })

        logger.info(f"Fetched {len(gemini_models)} Gemini models")
        return {"models": gemini_models}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to fetch Gemini models: {error_msg}")

        # If we can't fetch, return common models as fallback
        return {
            "models": [
                {"name": "gemini-2.0-flash", "display_name": "Gemini 2.0 Flash", "description": "Fast and versatile"},
                {"name": "gemini-2.5-pro", "display_name": "Gemini 2.5 Pro", "description": "High quality reasoning"},
                {"name": "gemini-1.5-pro", "display_name": "Gemini 1.5 Pro", "description": "Previous generation"},
                {"name": "gemini-1.5-flash", "display_name": "Gemini 1.5 Flash", "description": "Previous generation fast"},
            ],
            "error": error_msg,
        }


DEFAULT_MODELS_LISTS = {
    "chatgpt": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "grok": ["grok-4.3"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"],
}
