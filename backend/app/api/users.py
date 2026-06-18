from fastapi import APIRouter, Depends
from app.storage import store
from app.utils.auth import require_user

router = APIRouter()


@router.get("/me")
async def get_me(user: dict = Depends(require_user)):
    return {"id": user["id"], "username": user["username"], "target_band": user.get("target_band"), "native_language": user.get("native_language", "vi"), "llm_config": user.get("llm_config")}


@router.put("/me")
async def update_me(data: dict, user: dict = Depends(require_user)):
    if "target_band" in data:
        user["target_band"] = data["target_band"]
    if "native_language" in data:
        user["native_language"] = data["native_language"]
    store.save("users", user)
    return user


@router.get("/me/stats")
async def get_stats(user: dict = Depends(require_user)):
    uid = user["id"]
    essays = store.list("essays", filter_fn=lambda e: e.get("user_id") == uid)
    sessions = store.list("scoring_sessions", filter_fn=lambda s: any(e["id"] == s.get("essay_id") for e in essays))
    scored = [s for s in sessions if s.get("overall_band") is not None]
    latest = scored[0] if scored else None
    return {"total_essays": len(essays), "scored_essays": len(scored), "latest_band": latest.get("overall_band") if latest else None, "target_band": user.get("target_band")}
