import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.storage import store
from app.utils.auth import require_user
from app.llm.router import llm_complete
from app.services.scoring_service import get_llm_config
from app.utils.text_processing import json_loads

router = APIRouter()

# ── Pre-Writing Assistant ──
@router.post("/pre-write")
async def pre_writing_assistant(data: dict, user: dict = Depends(require_user)):
    """Analyze prompt before writing. Only activates when user requests."""
    task_type = data.get("task_type", "task2")
    prompt_text = data.get("prompt_text", "")

    if not prompt_text:
        raise HTTPException(status_code=400, detail="Prompt text is required")

    llm = get_llm_config(user)
    if not llm:
        raise HTTPException(status_code=400, detail="Please configure your LLM API key in Settings first")

    kb = await _get_kb(task_type)

    if task_type == "task1":
        sys_prompt = f"""You are an IELTS Task 1 pre-writing coach. Analyze the given prompt and help the user understand what to write.
DO NOT write the essay. Provide:
1. Task type identification (bar_chart, line_graph, pie_chart, table, process_diagram, map, mixed_charts)
2. Key trends/features to look for
3. Important comparisons to make
4. Suggested overview structure
5. Suggested paragraph structure
6. Common mistakes for this task type

KB reference: {kb}

JSON output: {{"task_type": "...", "chart_type": "...", "key_trends": "...", "comparisons": "...", "suggested_overview": "...", "suggested_paragraph_structure": "...", "common_mistakes": [...], "reasoning": "..."}}"""
    else:
        sys_prompt = f"""You are an IELTS Task 2 pre-writing coach. Analyze the prompt and guide the user's thinking.
DO NOT write the essay. Provide:
1. Essay type identification (opinion, discussion, discussion_opinion, advantages_disadvantages, positive_negative, two_part_question, problem_solution, direct_question)
2. Question analysis (what the prompt is really asking)
3. Required position/opinion
4. Suggested brainstorming ideas (3-5 key points)
5. Suggested essay structure (intro, body paragraphs, conclusion)
6. Common mistakes for this essay type

KB reference: {kb}

JSON output: {{"essay_type": "...", "question_analysis": "...", "required_position": "...", "brainstorming_ideas": [...], "suggested_structure": "...", "common_mistakes": [...], "reasoning": "..."}}"""

    try:
        resp = await llm_complete(llm, sys_prompt, f"Prompt:\n{prompt_text}", "json")
        return json_loads(resp.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Personalized Learning (Learn button) ──
@router.post("/analyze")
async def analyze_learning(user: dict = Depends(require_user)):
    """Analyze last N essays (max 10) and generate personalized improvement plan."""
    uid = user["id"]
    essays = store.list("essays", filter_fn=lambda e: e.get("user_id") == uid and e.get("status") == "completed")
    if not essays:
        raise HTTPException(status_code=400, detail="No completed essays found. Score some essays first.")

    recent = essays[:10]
    essay_texts = []
    scores = []
    for e in recent:
        sessions = store.list_sorted(
            "scoring_sessions",
            filter_fn=lambda s, eid=e["id"]: s.get("essay_id") == eid and s.get("overall_band") is not None,
            key=lambda s: s.get("started_at", ""),
        )
        if sessions:
            latest = sessions[0]
            essay_texts.append({"task_type": e["task_type"], "text": e["essay_text"][:2000], "band": latest["overall_band"]})
            scores.append(latest["overall_band"])

    if not essay_texts:
        raise HTTPException(status_code=400, detail="No scored essays found. Score some essays first.")

    llm = get_llm_config(user)
    if not llm:
        raise HTTPException(status_code=400, detail="Please configure your LLM API key in Settings first")

    sys_prompt = f"""You are a personalized IELTS learning coach. Analyze the user's recent essays and identify:
1. Recurring mistakes across essays
2. Hidden patterns (e.g., strong grammar but weak ideas, strong vocabulary but poor cohesion)
3. Priority weaknesses to address
4. Weekly improvement goals
5. Suggested exercises specific to their weaknesses
6. Recommended essay types to practice next

Recent essays (with bands): {json.dumps(essay_texts)}

JSON output: {{"recurring_mistakes": [{{"type": "...", "frequency": "often|sometimes", "examples": [...]}}], "hidden_patterns": [...], "priority_weaknesses": [{{"criterion": "...", "severity": "high|medium|low", "description": "..."}}], "weekly_goals": [...], "suggested_exercises": [...], "recommended_essay_types": [...], "estimated_next_band": float, "reasoning": "..."}}"""

    try:
        resp = await llm_complete(llm, sys_prompt, "Generate a personalized learning plan based on the essay history above.", "json")
        result = json_loads(resp.content)

        plan = {
            "id": f"plan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "user_id": uid,
            "focus_areas": result.get("priority_weaknesses", []),
            "recommended_exercises": result.get("suggested_exercises", []),
            "target_next_band": result.get("estimated_next_band"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "raw_response": resp.content,
        }
        store.save("learning_plans", plan)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Progress ──
@router.get("/progress")
async def get_progress(user: dict = Depends(require_user)):
    uid = user["id"]
    essays = store.list("essays", filter_fn=lambda e: e.get("user_id") == uid and e.get("status") == "completed")
    points = []
    for e in essays:
        sessions = store.list_sorted(
            "scoring_sessions",
            filter_fn=lambda s, eid=e["id"]: s.get("essay_id") == eid and s.get("overall_band") is not None,
            key=lambda s: s.get("started_at", ""),
        )
        if sessions:
            s = sessions[0]
            criteria = store.list("criteria_scores", filter_fn=lambda c: c.get("session_id") == s["id"])
            crit_map = {c["criterion"]: c["score"] for c in criteria}
            points.append({
                "date": s.get("completed_at", "")[:10],
                "overall_band": s["overall_band"],
                "task_response": crit_map.get("task_response"),
                "coherence_cohesion": crit_map.get("coherence_cohesion"),
                "lexical_resource": crit_map.get("lexical_resource"),
                "grammatical_range": crit_map.get("grammatical_range_accuracy"),
            })

    trend = "stable"
    if len(points) >= 2:
        first = points[0]["overall_band"] or 0
        last = points[-1]["overall_band"] or 0
        if last > first + 0.5:
            trend = "improving"
        elif last < first - 0.5:
            trend = "declining"

    strongest = None
    weakest = None
    if points:
        last = points[-1]
        sc = [(k, v) for k, v in last.items() if k not in ("date", "overall_band") and v is not None]
        if sc:
            strongest = max(sc, key=lambda x: x[1])[0]
            weakest = min(sc, key=lambda x: x[1])[0]

    return {"points": points, "trend": trend, "strongest_criterion": strongest, "weakest_criterion": weakest, "estimated_next_band": points[-1]["overall_band"] + 0.5 if points and points[-1].get("overall_band") else None}


@router.get("/plans")
async def list_plans(user: dict = Depends(require_user)):
    uid = user["id"]
    return store.list("learning_plans", filter_fn=lambda p: p.get("user_id") == uid)


async def _get_kb(task_type: str) -> str:
    try:
        from app.knowledge_base.retriever import retrieve
        return await retrieve(f"IELTS {task_type} essay structure writing tips", 5)
    except Exception:
        return ""
