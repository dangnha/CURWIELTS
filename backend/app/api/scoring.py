import asyncio
import logging
import json
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
from app.storage import store
from app.utils.auth import require_user
from app.services.scoring_service import run_scoring_pipeline, get_progress, get_latest_session
from app.llm.router import classify_llm_error

logger = logging.getLogger("app.api.scoring")
router = APIRouter()


@router.post("/{essay_id}/score")
async def trigger_scoring(essay_id: str, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")
    if essay.get("status") == "processing":
        raise HTTPException(status_code=409, detail="Scoring already in progress")
    if essay.get("status") == "completed":
        raise HTTPException(status_code=409, detail="This essay is already scored. Edit it to submit a new attempt.")

    cfg = user.get("llm_config")
    if not cfg or not cfg.get("api_key"):
        raise HTTPException(status_code=400, detail="Please configure your LLM API key in Settings first")

    provider = cfg.get("provider", "?")
    model = cfg.get("model", "?")
    logger.info("Scoring triggered — essay=%s task=%s provider=%s model=%s words=%d",
                essay_id[:8], essay.get("task_type"), provider, model, essay.get("word_count"))

    session_id = str(__import__("uuid").uuid4())
    session = {
        "id": session_id,
        "essay_id": essay_id,
        "status": "queued",
        "overall_band": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    store.save("scoring_sessions", session)

    async def _run_with_error_handling():
        try:
            logger.info("[%s] Pipeline starting...", session_id[:8])
            await run_scoring_pipeline(essay_id, essay, user)
            logger.info("[%s] Pipeline completed successfully", session_id[:8])
        except Exception as e:
            logger.exception("[%s] Pipeline FAILED: %s", session_id[:8], e)
            store.update("essays", essay_id, {"status": "failed"})
            store.update("scoring_sessions", session_id, {"status": "failed", "completed_at": datetime.now(timezone.utc).isoformat()})
            logger.error("[%s] ⚠ %s", session_id[:8], classify_llm_error(e))

    asyncio.create_task(_run_with_error_handling())
    return {"essay_id": essay_id, "session_id": session_id, "status": "queued"}


@router.get("/{essay_id}/band-upgrade")
async def get_band_upgrade(essay_id: str, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")

    session = get_latest_session(essay_id)
    if not session:
        raise HTTPException(status_code=404, detail="No scoring session found")

    session_id = session["id"]
    results = store.list("agent_results", filter_fn=lambda a: a.get("session_id") == session_id and a.get("agent_name") == "personalized_feedback")
    if not results:
        raise HTTPException(status_code=404, detail="Band upgrade suggestions not available yet")

    steps = results[0].get("metadata", {}).get("band_upgrade_suggestions", [])
    return {"essay_id": essay_id, "current_band": session.get("overall_band"), "steps": steps}


@router.get("/{essay_id}/score")
async def get_score(essay_id: str, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")

    session = get_latest_session(essay_id)
    if not session:
        return {"essay_id": essay_id, "session_id": "", "status": "pending", "overall_band": None, "criteria": []}

    session_id = session["id"]
    criteria_items = store.list("criteria_scores", filter_fn=lambda c: c.get("session_id") == session_id)
    progress = get_progress(session_id)

    # Attach sub-criteria scores from agent_results
    agent_results = store.list("agent_results", filter_fn=lambda a: a.get("session_id") == session_id)
    sub_criteria_map: dict[str, dict] = {}
    for ar in agent_results:
        sc = ar.get("metadata", {}).get("sub_criteria_scores")
        if sc and isinstance(sc, dict):
            sub_criteria_map[ar["agent_name"]] = sc

    return {
        "essay_id": essay_id,
        "session_id": session_id,
        "status": session["status"],
        "overall_band": session.get("overall_band"),
        "criteria": criteria_items,
        "sub_criteria_scores": sub_criteria_map,
        "progress": progress,
    }
