import time
from fastapi import APIRouter, Depends, HTTPException
from app.storage import store
from app.utils.auth import require_user
from app.llm.base import LLMConfig
from app.llm.router import llm_complete, classify_llm_error

router = APIRouter()


@router.get("/settings")
async def get_settings(user: dict = Depends(require_user)):
    return {
        "llm_config": user.get("llm_config"),
    }


@router.put("/settings")
async def update_settings(data: dict, user: dict = Depends(require_user)):
    """Save LLM configuration. Expected: {provider, api_key, model, temperature, max_tokens}"""
    user["llm_config"] = {
        "provider": data.get("provider", "gemini"),
        "api_key": data.get("api_key", ""),
        "model": data.get("model", "gemini-2.0-flash"),
        "temperature": data.get("temperature", 0.3),
        "max_tokens": data.get("max_tokens", 4096),
    }
    store.save("users", user)
    return {"llm_config": user["llm_config"]}


@router.post("/test-connection")
async def test_connection(data: dict | None = None, user: dict = Depends(require_user)):
    """Ping the configured LLM provider with a minimal request to verify the API key/model work.

    Accepts an optional {provider, api_key, model, temperature} body so Settings
    can test a not-yet-saved configuration; falls back to the user's saved config.
    """
    cfg_src = data or user.get("llm_config") or {}
    provider = cfg_src.get("provider", "gemini")
    api_key = cfg_src.get("api_key", "")
    if not api_key:
        return {"ok": False, "error": "No API key provided."}

    from app.llm.router import DEFAULT_MODELS
    cfg = LLMConfig(
        provider=provider,
        api_key=api_key,
        model=cfg_src.get("model") or DEFAULT_MODELS.get(provider, ""),
        temperature=cfg_src.get("temperature", 0.3),
        max_tokens=64,
    )

    t0 = time.time()
    try:
        resp = await llm_complete(cfg, "You are a connection test.", "Reply with the single word: ok", "text")
        latency_ms = int((time.time() - t0) * 1000)
        return {"ok": True, "provider": provider, "model": cfg.model, "latency_ms": latency_ms, "reply": resp.content.strip()[:50]}
    except Exception as e:
        return {"ok": False, "provider": provider, "model": cfg.model, "error": classify_llm_error(e)}


@router.get("/kb/status")
async def kb_status():
    try:
        from app.knowledge_base.vector_store import get_collection
        collection = get_collection()
        return {"status": "ready", "document_count": collection.count()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/kb/ingest")
async def trigger_ingest():
    from app.knowledge_base.ingest import ingest_knowledge_base
    return ingest_knowledge_base()
