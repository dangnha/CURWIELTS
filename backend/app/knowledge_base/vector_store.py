import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from pathlib import Path


_client: chromadb.ClientAPI | None = None
_collection_name = "ielts_knowledge"


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(name=_collection_name)


def add_chunks(chunks: list[str], metadata_list: list[dict], ids: list[str]):
    collection = get_collection()
    collection.add(documents=chunks, metadatas=metadata_list, ids=ids)


def collection_count() -> int:
    return get_collection().count()


def query_chunks(query_text: str, n_results: int = 5) -> list[str]:
    collection = get_collection()
    results = collection.query(query_texts=[query_text], n_results=n_results)
    docs = results.get("documents", [[]])[0]
    return docs if docs else []


def clear_collection():
    try:
        client = get_chroma_client()
        client.delete_collection(name=_collection_name)
    except Exception:
        pass
