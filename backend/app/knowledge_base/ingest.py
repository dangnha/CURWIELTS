from pathlib import Path
from app.config import settings
from app.knowledge_base.parser import parse_html_content, chunk_text


def ingest_knowledge_base():
    """Ingest all knowledge base files into ChromaDB."""
    from app.knowledge_base.vector_store import clear_collection, add_chunks

    kb_dir = settings.kb_source_dir
    if not kb_dir.exists():
        return {"status": "error", "message": f"KB directory not found: {kb_dir}"}

    all_files = list(kb_dir.rglob("*.txt")) + list(kb_dir.rglob("*.html"))
    if not all_files:
        return {"status": "error", "message": "No .txt or .html files found"}

    clear_collection()

    total_chunks = 0
    for file_path in all_files:
        try:
            raw = file_path.read_text(encoding="utf-8")
            text = parse_html_content(raw) if ".htm" in file_path.suffix else raw
            chunks = chunk_text(text)

            category = file_path.parent.name.lower().replace(" ", "_")
            metadata_list = [
                {
                    "source": str(file_path.relative_to(kb_dir)),
                    "category": category,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                for i in range(len(chunks))
            ]
            ids = [f"{file_path.stem}_{i}" for i in range(len(chunks))]

            add_chunks(chunks, metadata_list, ids)
            total_chunks += len(chunks)
        except Exception as e:
            print(f"Failed to ingest {file_path}: {e}")

    return {"status": "success", "files_processed": len(all_files), "total_chunks": total_chunks}
