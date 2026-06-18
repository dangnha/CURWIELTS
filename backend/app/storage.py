from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.config import settings


class JSONStore:
    """Simple JSON file-based storage. Each collection is a directory of .json files."""

    def __init__(self, base_dir: Path | None = None):
        self.base = base_dir or settings.data_dir
        self.base.mkdir(parents=True, exist_ok=True)

    def _collection_dir(self, collection: str) -> Path:
        d = self.base / collection
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _file_path(self, collection: str, doc_id: str) -> Path:
        return self._collection_dir(collection) / f"{doc_id}.json"

    def save(self, collection: str, data: dict) -> str:
        doc_id = data.get("id") or str(uuid.uuid4())
        data["id"] = doc_id
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        if "created_at" not in data:
            data["created_at"] = datetime.now(timezone.utc).isoformat()
        path = self._file_path(collection, doc_id)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return doc_id

    def get(self, collection: str, doc_id: str) -> dict | None:
        path = self._file_path(collection, doc_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self, collection: str, filter_fn=None) -> list[dict]:
        dir_ = self._collection_dir(collection)
        results = []
        for f in sorted(dir_.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if filter_fn is None or filter_fn(data):
                    results.append(data)
            except Exception:
                continue
        return results

    def list_sorted(self, collection: str, filter_fn=None, key=None, reverse: bool = True) -> list[dict]:
        """Like list(), but ordered by `key` (applied to each dict) instead of filename order.

        Filenames are UUIDs, not timestamps, so list() order is effectively
        arbitrary with respect to creation time — use this whenever "most
        recent" actually matters (e.g. picking the latest scoring session).
        """
        items = self.list(collection, filter_fn=filter_fn)
        return sorted(items, key=key, reverse=reverse)

    def delete(self, collection: str, doc_id: str) -> bool:
        path = self._file_path(collection, doc_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def update(self, collection: str, doc_id: str, updates: dict) -> dict | None:
        data = self.get(collection, doc_id)
        if data is None:
            return None
        data.update(updates)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        path = self._file_path(collection, doc_id)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data


store = JSONStore()
