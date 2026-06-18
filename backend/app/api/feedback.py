from fastapi import APIRouter, Depends, HTTPException
from app.storage import store
from app.utils.auth import require_user
from app.services.scoring_service import get_latest_session

router = APIRouter()


@router.get("/{essay_id}/feedback")
async def get_feedback(essay_id: str, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")

    session = get_latest_session(essay_id)
    if not session:
        raise HTTPException(status_code=404, detail="No scoring session found")

    session_id = session["id"]
    agent_results = store.list("agent_results", filter_fn=lambda a: a.get("session_id") == session_id and a.get("agent_name") == "personalized_feedback")
    if not agent_results:
        return {"feedback": None}

    # run_agent() already safely parsed the model's response (handling markdown
    # fences/preamble) into `metadata` when the agent ran — reuse that instead
    # of re-parsing raw_response again here, which can fail on output the
    # pipeline already parsed successfully once.
    metadata = agent_results[0].get("metadata", {})
    return {
        "overall_assessment": metadata.get("overall_assessment", ""),
        "criterion_feedback": metadata.get("criterion_feedback", {}),
        "priority_weakness": metadata.get("priority_weakness", ""),
        "recommended_exercises": metadata.get("recommended_exercises", []),
        "reasoning": agent_results[0].get("reasoning"),
        "paragraph_analysis": metadata.get("paragraph_analysis", []),
        "structure_improvement": metadata.get("structure_improvement", {}),
        "vocabulary_table": metadata.get("vocabulary_table", []),
        "sentence_diversity": metadata.get("sentence_diversity", []),
        "coherence_improvement": metadata.get("coherence_improvement", []),
        "sample_essays": metadata.get("sample_essays", {}),
        "band_upgrade_suggestions": metadata.get("band_upgrade_suggestions", []),
    }
