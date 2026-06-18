import uuid
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.storage import store
from app.utils.auth import require_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger("app.api.essays")


class EssayCreate(BaseModel):
    task_type: str  # "task1" or "task2"
    essay_text: str
    prompt_text: str | None = None
    exam_label: str | None = None


class EssayUpdate(BaseModel):
    essay_text: str | None = None
    prompt_text: str | None = None
    exam_label: str | None = None


EDITABLE_STATUSES = ("pending", "failed")


@router.post("")
async def create_essay(data: EssayCreate, user: dict = Depends(require_user)):
    word_count = len(data.essay_text.split())
    logger.info("Essay submitted — user=%s task=%s words=%d", user.get("username", "?"), data.task_type, word_count)
    essay = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "task_type": data.task_type,
        "essay_type": None,
        "prompt_text": data.prompt_text,
        "essay_text": data.essay_text,
        "exam_label": data.exam_label,
        "word_count": word_count,
        "image_path": None,
        "status": "pending",
    }
    store.save("essays", essay)
    return essay


@router.post("/task1")
async def create_task1(
    essay_text: str = Form(...),
    prompt_text: str = Form(None),
    exam_label: str = Form(None),
    image: UploadFile | None = File(None),
    user: dict = Depends(require_user),
):
    word_count = len(essay_text.split())
    image_path = None
    if image and image.filename:
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(image.filename).suffix or ".png"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = settings.uploads_dir / filename
        with filepath.open("wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = str(filepath.relative_to(settings.base_dir))

    essay = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "task_type": "task1",
        "essay_type": None,
        "prompt_text": prompt_text,
        "essay_text": essay_text,
        "exam_label": exam_label,
        "word_count": word_count,
        "image_path": image_path,
        "status": "pending",
    }
    store.save("essays", essay)
    return essay


@router.get("")
async def list_essays(page: int = 1, page_size: int = 10, task_type: str | None = None, status: str | None = None, user: dict = Depends(require_user)):
    def filt(e):
        if e.get("user_id") != user["id"]:
            return False
        if task_type and e.get("task_type") != task_type:
            return False
        if status and e.get("status") != status:
            return False
        return True

    all_items = store.list("essays", filter_fn=filt)
    total = len(all_items)
    start = (page - 1) * page_size
    items = all_items[start:start + page_size]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{essay_id}")
async def get_essay(essay_id: str, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")
    return essay


@router.patch("/{essay_id}")
async def update_essay(essay_id: str, data: EssayUpdate, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")
    if essay.get("status") not in EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Only pending or failed essays can be edited. Already-scored essays are read-only.")

    updates: dict = {"status": "pending", "essay_type": None}
    if data.essay_text is not None:
        updates["essay_text"] = data.essay_text
        updates["word_count"] = len(data.essay_text.split())
    if data.prompt_text is not None:
        updates["prompt_text"] = data.prompt_text
    if data.exam_label is not None:
        updates["exam_label"] = data.exam_label

    return store.update("essays", essay_id, updates)


@router.patch("/{essay_id}/task1")
async def update_task1(
    essay_id: str,
    essay_text: str = Form(...),
    prompt_text: str = Form(None),
    exam_label: str = Form(None),
    image: UploadFile | None = File(None),
    user: dict = Depends(require_user),
):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")
    if essay.get("status") not in EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail="Only pending or failed essays can be edited. Already-scored essays are read-only.")

    updates: dict = {
        "status": "pending",
        "essay_type": None,
        "essay_text": essay_text,
        "prompt_text": prompt_text,
        "exam_label": exam_label,
        "word_count": len(essay_text.split()),
    }
    if image and image.filename:
        settings.uploads_dir.mkdir(parents=True, exist_ok=True)
        ext = Path(image.filename).suffix or ".png"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = settings.uploads_dir / filename
        with filepath.open("wb") as f:
            shutil.copyfileobj(image.file, f)
        updates["image_path"] = str(filepath.relative_to(settings.base_dir))

    return store.update("essays", essay_id, updates)


@router.delete("/{essay_id}")
async def delete_essay(essay_id: str, user: dict = Depends(require_user)):
    essay = store.get("essays", essay_id)
    if not essay or essay.get("user_id") != user["id"]:
        raise HTTPException(status_code=404, detail="Essay not found")
    store.delete("essays", essay_id)
    return {"status": "deleted"}
