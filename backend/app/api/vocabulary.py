from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.storage import store
from app.utils.auth import require_user
import io
import csv
import json

router = APIRouter()


@router.get("")
async def list_vocabulary(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    cefr_level: str | None = None,
    user: dict = Depends(require_user),
):
    uid = user["id"]
    essays = store.list("essays", filter_fn=lambda e: e.get("user_id") == uid)
    essay_ids = {e["id"] for e in essays}

    def filt(v):
        if v.get("essay_id") not in essay_ids:
            return False
        if cefr_level and v.get("cefr_level") != cefr_level:
            return False
        return True

    items = store.list("vocabulary_items", filter_fn=filt)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start:start + page_size]

    # Stats
    by_cefr = {}
    academic_count = 0
    error_count = 0
    for v in items:
        if v.get("cefr_level"):
            by_cefr[v["cefr_level"]] = by_cefr.get(v["cefr_level"], 0) + 1
        if v.get("is_academic"):
            academic_count += 1
        if v.get("usage_accuracy") is not None and v["usage_accuracy"] < 0.5:
            error_count += 1

    return {
        "items": page_items,
        "stats": {"total_unique": total, "by_cefr": by_cefr, "academic_count": academic_count, "error_count": error_count},
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats")
async def vocabulary_stats(user: dict = Depends(require_user)):
    uid = user["id"]
    essays = store.list("essays", filter_fn=lambda e: e.get("user_id") == uid)
    essay_ids = {e["id"] for e in essays}
    items = store.list("vocabulary_items", filter_fn=lambda v: v.get("essay_id") in essay_ids)

    by_cefr = {}
    ac = 0
    ec = 0
    for v in items:
        if v.get("cefr_level"):
            by_cefr[v["cefr_level"]] = by_cefr.get(v["cefr_level"], 0) + 1
        if v.get("is_academic"):
            ac += 1
        if v.get("usage_accuracy") is not None and v["usage_accuracy"] < 0.5:
            ec += 1

    return {"total_unique": len({v["word"] for v in items}), "by_cefr": by_cefr, "academic_count": ac, "error_count": ec}


@router.post("/export")
async def export_vocabulary(format: str = Query("json"), user: dict = Depends(require_user)):
    uid = user["id"]
    essays = store.list("essays", filter_fn=lambda e: e.get("user_id") == uid)
    essay_ids = {e["id"] for e in essays}
    items = store.list("vocabulary_items", filter_fn=lambda v: v.get("essay_id") in essay_ids)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["word", "pos", "cefr_level", "ipa", "is_academic", "definition", "example_sentence", "context_sentence", "synonyms", "usage_accuracy"])
        for v in items:
            writer.writerow([v.get("word"), v.get("pos"), v.get("cefr_level"), v.get("ipa"), v.get("is_academic"), v.get("definition", ""), v.get("example_sentence", ""), v.get("context_sentence", ""), ",".join(v.get("synonyms", [])), v.get("usage_accuracy")])
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=vocabulary.csv"})

    if format == "excel":
        try:
            import openpyxl
        except ImportError:
            return {"error": "openpyxl not installed"}
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["word", "pos", "cefr_level", "ipa", "is_academic", "definition", "example_sentence", "context_sentence", "synonyms", "usage_accuracy"])
        for v in items:
            ws.append([v.get("word"), v.get("pos"), v.get("cefr_level"), v.get("ipa"), v.get("is_academic"), v.get("definition", ""), v.get("example_sentence", ""), v.get("context_sentence", ""), ",".join(v.get("synonyms", [])), v.get("usage_accuracy")])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=vocabulary.xlsx"})

    return items
