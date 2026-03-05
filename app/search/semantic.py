"""Semantic search engine using sentence-transformers + ChromaDB."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Passage, Source
from app.nlp.embeddings import query_similar


def search_semantic(
    db: Session,
    query: str,
    source_id: UUID | None = None,
    limit: int = 20,
    similarity_threshold: float = 0.3,
) -> dict:
    """Find passages semantically similar to the query.

    Returns:
        dict with keys: query, total, results (each with similarity score)
    """
    where = None
    if source_id:
        where = {"source_id": str(source_id)}

    chroma_results = query_similar(query, n_results=limit, where=where)

    if not chroma_results["ids"] or not chroma_results["ids"][0]:
        return {"query": query, "total": 0, "results": []}

    ids = chroma_results["ids"][0]
    distances = chroma_results["distances"][0]

    # ChromaDB cosine distance: 0 = identical, 2 = opposite
    # Convert to similarity: similarity = 1 - distance
    scored = []
    for passage_id, distance in zip(ids, distances):
        similarity = 1.0 - distance
        if similarity >= similarity_threshold:
            scored.append((passage_id, similarity))

    if not scored:
        return {"query": query, "total": 0, "results": []}

    passage_ids = [pid for pid, _ in scored]
    similarity_map = {pid: sim for pid, sim in scored}

    # Fetch passages with source info from PostgreSQL
    rows = (
        db.query(Passage, Source)
        .join(Source, Source.id == Passage.source_id)
        .filter(Passage.id.in_(passage_ids))
        .all()
    )

    # Build lookup and preserve ChromaDB ranking order
    row_map = {str(p.id): (p, s) for p, s in rows}

    results = []
    for pid in passage_ids:
        if pid not in row_map:
            continue
        passage, source = row_map[pid]
        results.append({
            "passage_id": str(passage.id),
            "text": passage.text,
            "location_label": passage.location_label,
            "source": {
                "id": str(source.id),
                "title": source.title,
                "type": source.type,
            },
            "similarity": round(similarity_map[pid], 4),
        })

    return {
        "query": query,
        "total": len(results),
        "results": results,
    }
