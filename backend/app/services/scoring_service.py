import asyncio
import json
import math
import uuid
import logging
import traceback
from datetime import datetime, timezone

from app.config import settings
from app.llm.base import LLMConfig
from app.llm.router import llm_complete
from app.llm.router import DEFAULT_MODELS
from app.storage import store
from app.utils.text_processing import json_loads

logger = logging.getLogger("app.services.scoring")

_active_sessions: dict[str, dict] = {}

AGENT_PIPELINE = [
    "coherence_cohesion", "lexical_resource", "grammatical_range",
    "task_response", "vocabulary_extraction", "error_analysis",
    "personalized_feedback",
]


def get_llm_config(user: dict) -> LLMConfig | None:
    cfg = user.get("llm_config")
    if cfg and cfg.get("api_key"):
        return LLMConfig(
            provider=cfg.get("provider", "gemini"),
            api_key=cfg["api_key"],
            model=cfg.get("model", DEFAULT_MODELS.get(cfg.get("provider", "gemini"), "gemini-2.0-flash")),
            temperature=cfg.get("temperature", 0.3),
            max_tokens=cfg.get("max_tokens", settings.max_tokens),
        )
    return None


async def run_agent(agent_name: str, system_prompt: str, user_prompt: str, llm: LLMConfig, session_id: str, image_path: str | None = None) -> dict:
    logger.info(f"[{session_id[:8]}] Starting agent: {agent_name}")
    if session_id not in _active_sessions:
        _active_sessions[session_id] = {"agents": {}, "status": "running"}
    _active_sessions[session_id]["agents"][agent_name] = {"status": "running"}

    try:
        try:
            resp = await llm_complete(llm, system_prompt, user_prompt, "json", image_path=image_path)
        except Exception as e:
            msg = str(e).lower()
            if "json_validate_failed" in msg or "max completion tokens" in msg:
                logger.warning(f"[{session_id[:8]}] Agent {agent_name} JSON mode failed, retrying without JSON format")
                resp = await llm_complete(llm, system_prompt, user_prompt, "text", image_path=image_path)
            else:
                raise

        logger.info(f"[{session_id[:8]}] Agent {agent_name} response: {resp.content[:300]}...")
        logger.info(f"[{session_id[:8]}] Agent {agent_name} tokens: {resp.total_tokens}, latency: {resp.latency_ms}ms")

        data = json_loads(resp.content)
        logger.info(f"[{session_id[:8]}] Agent {agent_name} parsed keys: {list(data.keys())} band_score={data.get('band_score')}")

        result = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "agent_name": agent_name,
            "band_score": data.get("band_score"),
            "raw_response": resp.content,
            "reasoning": data.get("reasoning", ""),
            "confidence": data.get("confidence", 0.8),
            "metadata": {k: v for k, v in data.items() if k not in ("band_score", "reasoning", "confidence")},
        }
        store.save("agent_results", result)
        _active_sessions[session_id]["agents"][agent_name] = {"status": "completed", "band": result.get("band_score")}
        logger.info(f"[{session_id[:8]}] Agent {agent_name} completed. band={result.get('band_score')}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"[{session_id[:8]}] Agent {agent_name} JSON parse error: {e}")
        logger.error(f"[{session_id[:8]}] Raw response was: {resp.content[:500]}")
        _active_sessions[session_id]["agents"][agent_name] = {"status": "failed", "error": f"JSON parse: {e}"}
        return {"agent_name": agent_name, "error": f"JSON parse: {e}", "band_score": None, "metadata": {}}
    except Exception as e:
        logger.error(f"[{session_id[:8]}] Agent {agent_name} FAILED: {e}")
        logger.error(f"[{session_id[:8]}] Traceback: {traceback.format_exc()}")
        _active_sessions[session_id]["agents"][agent_name] = {"status": "failed", "error": str(e)}
        return {"agent_name": agent_name, "error": str(e), "band_score": None, "metadata": {}}


async def run_scoring_pipeline(essay_id: str, essay: dict, user: dict):
    llm = get_llm_config(user)
    if not llm:
        raise ValueError("No LLM configured. Please set API key in Settings.")

    session_id = str(uuid.uuid4())
    logger.info(f"[{session_id[:8]}] === START SCORING for essay {essay_id[:8]}, provider={llm.provider}, model={llm.model} ===")

    session = {
        "id": session_id,
        "essay_id": essay_id,
        "status": "in_progress",
        "overall_band": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    store.save("scoring_sessions", session)
    store.update("essays", essay_id, {"status": "processing"})
    _active_sessions[session_id] = {"agents": {}, "status": "running"}

    essay_text = essay["essay_text"]
    prompt_text = essay.get("prompt_text", "")
    task_type = essay["task_type"]

    image_path = None
    if task_type == "task1" and essay.get("image_path"):
        candidate = settings.base_dir / essay["image_path"]
        if candidate.exists():
            image_path = str(candidate)

    kb_context = _get_kb_context(task_type)
    trimmed_essay = essay_text
    if llm.provider == "groq":
        # Free-tier Groq has 8000 TPM — a single request can't exceed it.
        # Strip KB context completely and cap the essay so we stay under.
        kb_context = ""
        if len(essay_text) > 2200:
            trimmed_essay = essay_text[:2200] + "\n\n[Essay truncated for Groq free-tier token budget — the first 2200 chars are scored.]"
            logger.warning(f"[{session_id[:8]}] Essay truncated from {len(essay_text)} to {len(trimmed_essay)} chars for Groq TPM limit")

    try:
        # Phase 1: sequential scoring — Groq free-tier has low TPM limits, so we run
        # agents one at a time with a gap to stay under the per-minute token budget.
        cc_sys = _build_system_prompt("coherence_cohesion", task_type, kb_context)
        lr_sys = _build_system_prompt("lexical_resource", task_type, kb_context)
        gra_sys = _build_system_prompt("grammatical_range", task_type, kb_context)

        phase1_user = f"Essay:\n{trimmed_essay}"

        if llm.provider == "groq":
            cc_result = await run_agent("coherence_cohesion", cc_sys, phase1_user, llm, session_id)
            await asyncio.sleep(6)
            lr_result = await run_agent("lexical_resource", lr_sys, phase1_user, llm, session_id)
            await asyncio.sleep(6)
            gra_result = await run_agent("grammatical_range", gra_sys, phase1_user, llm, session_id)
            results = [cc_result, lr_result, gra_result]
        else:
            results = await asyncio.gather(
                run_agent("coherence_cohesion", cc_sys, phase1_user, llm, session_id),
                run_agent("lexical_resource", lr_sys, phase1_user, llm, session_id),
                run_agent("grammatical_range", gra_sys, phase1_user, llm, session_id),
            )

        # Log phase 1 results
        logger.info(f"[{session_id[:8]}] Phase 1 results:")
        for r in results:
            logger.info(f"  {r.get('agent_name')}: band={r.get('band_score')}, error={r.get('error', 'none')}, metadata_keys={list(r.get('metadata', {}).keys())[:5]}")

        # Phase 1b: Task Response (also detects essay type + structure, replacing the old separate agent)
        tr_sys = _build_system_prompt("task_response", task_type, kb_context)
        tr_user = f"{'Prompt: ' + prompt_text + chr(10) if prompt_text else ''}Essay:\n{trimmed_essay}"
        if image_path:
            tr_user += "\n\n(The Task 1 chart/graph/map/process image is attached — use it to verify the data described in the essay.)"
        tr_result = await run_agent("task_response", tr_sys, tr_user, llm, session_id, image_path=image_path)
        logger.info(f"[{session_id[:8]}] Task Response: band={tr_result.get('band_score')}, error={tr_result.get('error')}")

        essay_type = tr_result.get("metadata", {}).get("essay_type", "")
        if essay_type:
            store.update("essays", essay_id, {"essay_type": essay_type})
            logger.info(f"[{session_id[:8]}] Detected essay type: {essay_type}")

        # Phase 2: Vocab + Error
        vocab_result, err_result = await asyncio.gather(
            run_agent("vocabulary_extraction", _build_vocab_prompt(), f"Essay:\n{trimmed_essay}", llm, session_id),
            run_agent("error_analysis", _build_error_prompt(), f"Essay:\n{trimmed_essay}", llm, session_id),
        )
        logger.info(f"[{session_id[:8]}] Vocab: {len(vocab_result.get('metadata', {}).get('vocabulary', []))} words")
        logger.info(f"[{session_id[:8]}] Errors: {len(err_result.get('metadata', {}).get('errors', []))} items")

        # Store vocabulary
        vocab_count = 0
        if vocab_result and not vocab_result.get("error"):
            for item in vocab_result.get("metadata", {}).get("vocabulary", []):
                vi = {
                    "id": str(uuid.uuid4()),
                    "essay_id": essay_id,
                    "session_id": session_id,
                    "word": item.get("word", ""),
                    "pos": item.get("pos") or item.get("part_of_speech", ""),
                    "cefr_level": item.get("cefr_level", ""),
                    "ipa": item.get("ipa") or item.get("ipa_pronunciation", ""),
                    "is_academic": item.get("is_academic", False),
                    "context_sentence": item.get("context_sentence", ""),
                    "definition": item.get("definition", ""),
                    "example_sentence": item.get("example_sentence", ""),
                    "synonyms": item.get("synonyms", []),
                    "collocations": item.get("collocations", []),
                    "usage_accuracy": item.get("usage_accuracy"),
                    "suggestion": item.get("suggestion"),
                }
                store.save("vocabulary_items", vi)
                vocab_count += 1
        logger.info(f"[{session_id[:8]}] Stored {vocab_count} vocabulary items")

        # Store errors
        err_count = 0
        if err_result and not err_result.get("error"):
            for err in err_result.get("metadata", {}).get("errors", []):
                er = {
                    "id": str(uuid.uuid4()),
                    "essay_id": essay_id,
                    "session_id": session_id,
                    "error_type": err.get("error_type", "grammar"),
                    "severity": err.get("severity", "minor"),
                    "error_text": err.get("error_text", ""),
                    "correction": err.get("correction"),
                    "explanation": err.get("explanation"),
                }
                store.save("error_records", er)
                err_count += 1
        logger.info(f"[{session_id[:8]}] Stored {err_count} error records")

        # Store criteria scores
        agent_criteria_map = {
            "task_response": tr_result,
            "coherence_cohesion": results[0],
            "lexical_resource": results[1],
            "grammatical_range": results[2],
        }
        criteria_map = {"task_response": "task_response", "coherence_cohesion": "coherence_cohesion", "lexical_resource": "lexical_resource", "grammatical_range": "grammatical_range_accuracy"}
        criteria_scores = {}

        for agent_name, r in agent_criteria_map.items():
            crit_name = criteria_map[agent_name]
            if r and not r.get("error") and r.get("band_score") is not None:
                score = float(r["band_score"])
                strengths = r.get("metadata", {}).get("strengths", [])
                weaknesses = r.get("metadata", {}).get("weaknesses", [])
                feedback = r.get("reasoning", "")
            else:
                error_detail = r.get("error", "Unknown error") if r else "Agent did not return results"
                score = 5.0
                strengths = []
                weaknesses = [f"Scoring agent failed: {error_detail}. Please try again or check your API key."]
                feedback = f"This criterion could not be evaluated because the AI agent encountered an error: {error_detail}"
                logger.warning(f"[{session_id[:8]}] {agent_name} FAILED: error={error_detail}")

            criteria_scores[crit_name] = score
            cs = {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "criterion": crit_name,
                "score": score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "detailed_feedback": feedback,
            }
            store.save("criteria_scores", cs)

        logger.info(f"[{session_id[:8]}] Criteria scores: {criteria_scores}")

        # Phase 3: overall band is a deterministic average + IELTS rounding — no LLM call needed
        # (this used to call a "band_score_aggregator" agent, but that's pure arithmetic the
        # model wasn't adding judgment to, just burning a call to roughly reproduce _calculate_band).
        overall_band = _calculate_band(criteria_scores)
        logger.info(f"[{session_id[:8]}] Overall band (calculated): {overall_band}")

        # Feedback + band upgrade suggestions, combined into a single call
        feedback_result = await run_agent("personalized_feedback", _build_feedback_prompt(criteria_scores, overall_band, task_type), f"Essay:\n{trimmed_essay}", llm, session_id)
        logger.info(f"[{session_id[:8]}] Feedback: keys={list(feedback_result.get('metadata', {}).keys())[:5]}")

        # Finalize
        session["overall_band"] = overall_band
        session["status"] = "completed"
        session["completed_at"] = datetime.now(timezone.utc).isoformat()
        store.save("scoring_sessions", session)
        store.update("essays", essay_id, {"status": "completed"})

        _active_sessions[session_id]["status"] = "completed"
        _active_sessions[session_id]["overall_band"] = overall_band

        logger.info(f"[{session_id[:8]}] === SCORING COMPLETED. Band: {overall_band} ===")
        return {"session_id": session_id, "overall_band": overall_band, "status": "completed"}

    except Exception as e:
        logger.exception(f"[{session_id[:8]}] SCORING FAILED: {e}")
        session["status"] = "failed"
        store.save("scoring_sessions", session)
        store.update("essays", essay_id, {"status": "failed"})
        _active_sessions[session_id]["status"] = "failed"
        _active_sessions[session_id]["error"] = str(e)
        raise


def _get_kb_context(task_type: str) -> str:
    try:
        from app.knowledge_base.vector_store import query_chunks
        docs = query_chunks(f"IELTS {task_type} scoring criteria band descriptors", n_results=3)
        ctx = "\n\n".join(docs) if docs else ""
        return ctx[:1200]
    except Exception:
        logger.exception("KB context retrieval failed")
        return ""


def _calculate_band(criteria: dict) -> float:
    """Average the 4 criteria and round per official IELTS rules.

    IELTS always rounds UP to the nearest 0.5 when the average isn't
    already on a 0.5 step (e.g. 6.25 -> 6.5, 6.75 -> 7.0) — it never rounds
    down, and never rounds half-to-even like Python's builtin round().
    """
    if not criteria:
        return 5.0
    avg = sum(criteria.values()) / len(criteria)
    doubled = round(avg * 2, 6)  # clear floating-point noise before ceil
    return math.ceil(doubled) / 2


# ── Prompt builders ──

def _build_system_prompt(agent: str, task_type: str, kb: str) -> str:
    prompts = {
        "coherence_cohesion": f"""IELTS Coherence & Cohesion examiner. Evaluate paragraph organization, logical flow, cohesive devices (linking words, referencing, substitution).

{("REF: " + kb[:400]) if kb else ""}

JSON ONLY:
{{"band_score":0-9,"sub_criteria_scores":{{"logical_organization":0-9,"effective_intro_conclusion":0-9,"supported_main_points":0-9,"cohesive_devices_usage":0-9,"paragraphing":0-9}},"cohesive_devices_used":[],"cohesive_device_issues":[],"strengths":[],"weaknesses":[],"reasoning":"...","confidence":0.8}}""",

        "lexical_resource": f"""IELTS Lexical Resource examiner. Evaluate vocabulary range, precision, collocation, style/register, spelling, uncommon words, repetition.

{("REF: " + kb[:400]) if kb else ""}

JSON ONLY:
{{"band_score":0-9,"sub_criteria_scores":{{"vocabulary_range":0-9,"lexical_accuracy":0-9,"spelling_word_formation":0-9}},"collocation_accuracy":"...","style_appropriateness":"...","repetition_issues":[],"notable_vocabulary":[],"strengths":[],"weaknesses":[],"reasoning":"...","confidence":0.8}}""",

        "grammatical_range": f"""IELTS Grammatical Range & Accuracy examiner. Evaluate sentence structure variety, grammar accuracy, punctuation. Find specific errors.

{("REF: " + kb[:400]) if kb else ""}

JSON ONLY:
{{"band_score":0-9,"sub_criteria_scores":{{"sentence_structure_variety":0-9,"grammar_accuracy":0-9,"punctuation_usage":0-9}},"sentence_variety":"...","grammar_accuracy_level":"...","grammar_errors":[{{"error_type":"tense","incorrect_text":"...","correction":"...","explanation":"..."}}],"strengths":[],"weaknesses":[],"reasoning":"...","confidence":0.8}}""",

        "task_response": f"""IELTS Task Achievement/Response examiner. Check: addresses all prompt parts, clear position, idea development, supporting evidence, word count. Detect essay type and paragraph structure.

Task: {task_type}
{("REF: " + kb[:400]) if kb else ""}

JSON ONLY:
{{"band_score":0-9,"sub_criteria_scores":{{"relevance_to_prompt":0-9,"key_data_selection":0-9,"depth_of_ideas":0-9,"appropriateness_of_format":0-9,"data_accuracy":0-9,"appropriate_word_count":0-9}},"position_clarity":"...","idea_development":"...","task_coverage":"...","missing_requirements":[],"essay_type":"opinion_essay","has_introduction":true,"has_body_paragraphs":true,"has_conclusion_or_overview":true,"paragraph_count":4,"structure_issues":[],"strengths":[],"weaknesses":[],"reasoning":"...","confidence":0.8}}""",
    }
    return prompts.get(agent, prompts.get("task_response", ""))


def _build_vocab_prompt() -> str:
    return """IELTS vocabulary analyst. Extract notable vocabulary (min 5 words). Per word: word, pos (noun/verb/adj/adv), cefr_level, ipa, is_academic, definition, example_sentence, context_sentence, synonyms[], collocations[], usage_accuracy (0-1), suggestion (if misused). JSON: {"vocabulary":[{...}],"grammar_structures":[{"type":"complex_sentence","example":"..."}],"linking_devices":[],"reasoning":"..."}"""


def _build_error_prompt() -> str:
    return """IELTS error analyst. Find ALL errors: grammar, spelling, punctuation, word_choice, collocation, coherence. Per error: error_type, severity(minor/moderate/severe), error_text, correction, explanation. JSON: {"errors":[{...}],"error_summary":{"total_errors":0,"by_type":{},"by_severity":{}},"reasoning":"..."}"""


def _build_feedback_prompt(criteria: dict, overall: float, task_type: str) -> str:
    higher = [b for b in [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0] if b > overall]
    targets = higher[:2]
    return f"""IELTS tutor. Generate comprehensive feedback. Scores: {json.dumps(criteria)}, Overall: {overall}, Task: {task_type}, Targets: {targets}. Include: overall_assessment, paragraph_analysis[{{paragraph_label,original_text,comments{{task_response,coherence_cohesion,grammatical_range,lexical_resource}},how_to_rewrite}}], structure_improvement{{task_type,key_tips[],recommended_outline[{{section,example_topic_sentence}}]}}, vocabulary_table[{{word,word_type,definition_vn}}]x10, sentence_diversity[{{grammar_structure,original_sentence,rephrased_sentence}}]x5, coherence_improvement[{{original_text,improved_text,explanation}}]x5, band_upgrade_suggestions[{{target_band,required_improvements[],example_revisions[]}}], sample_essays{{corrected_essay,model_essay_band_8_9}}, criterion_feedback{{task_response,coherence_cohesion,lexical_resource,grammatical_range_accuracy}}, priority_weakness, recommended_exercises[], reasoning. JSON ONLY."""


def get_latest_session(essay_id: str) -> dict | None:
    """Return the most recent scoring_session for an essay, ordered by started_at.

    store.list() sorts by filename (a UUID), not by time, so sessions[0]
    after a plain list() is not reliably "the latest" — this is the one
    place that resolves "current session for this essay" correctly.
    """
    sessions = store.list_sorted(
        "scoring_sessions",
        filter_fn=lambda s: s.get("essay_id") == essay_id,
        key=lambda s: s.get("started_at", ""),
    )
    return sessions[0] if sessions else None


def get_progress(session_id: str) -> dict | None:
    session = _active_sessions.get(session_id)
    if session is None:
        return None
    agents = session.get("agents", {})
    completed = sum(1 for a in agents.values() if a.get("status") == "completed")
    return {**session, "completed": completed, "total": len(AGENT_PIPELINE)}
