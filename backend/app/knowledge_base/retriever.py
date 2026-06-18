from app.knowledge_base.vector_store import query_chunks


async def retrieve(query: str, top_k: int = 5) -> str:
    """Retrieve relevant knowledge base snippets for a query."""
    try:
        docs = query_chunks(query, n_results=top_k)
        if docs:
            return "\n\n---\n\n".join(docs)
    except Exception:
        pass
    return ""


async def retrieve_for_criterion(criterion: str, task_type: str, top_k: int = 5) -> str:
    """Retrieve KB snippets relevant to a specific IELTS criterion."""
    query_map = {
        "task_response": f"IELTS {task_type} task response/achievement scoring criteria band descriptors common errors",
        "coherence_cohesion": f"IELTS {task_type} coherence cohesion band descriptors linking words paragraph organization",
        "lexical_resource": f"IELTS {task_type} lexical resource vocabulary range collocation spelling word choice",
        "grammatical_range": f"IELTS {task_type} grammatical range accuracy sentence structures tense punctuation",
        "essay_structure": f"IELTS {task_type} essay structure introduction body conclusion PEEL method",
    }
    query = query_map.get(criterion, criterion)
    return await retrieve(query, top_k)
