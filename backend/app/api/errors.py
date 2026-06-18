from fastapi import APIRouter, Depends, HTTPException
from app.storage import store
from app.utils.auth import require_user
from app.services.scoring_service import get_latest_session

router = APIRouter()


@router.get("/{essay_id}/errors")
async def get_errors(essay_id: str, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")

    session = get_latest_session(essay_id)
    if not session:
        return []

    return store.list("error_records", filter_fn=lambda e: e.get("session_id") == session["id"])
