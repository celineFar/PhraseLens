"""Exact match search engine using the LemmaIndex."""

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import LemmaIndex, Passage, Source
from app.nlp.pipeline import lemmatize_query


def search_exact(
    db: Session,
    query: str,
    source_id: UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search for passages matching the query using lemma normalization.

    For multi-word queries, finds passages that contain ALL query lemmas.

    Returns:
        dict with keys: query, lemmas, total, results
    """
    query_lemmas = lemmatize_query(query)

    if not query_lemmas:
        return {"query": query, "lemmas": [], "total": 0, "results": []}

    # Find passage IDs that contain ALL query lemmas
    # For each lemma, get the set of passage IDs, then intersect
    base_query = (
        db.query(LemmaIndex.passage_id)
        .filter(LemmaIndex.lemma.in_(query_lemmas))
    )

    if source_id:
        base_query = (
            base_query
            .join(Passage, Passage.id == LemmaIndex.passage_id)
            .filter(Passage.source_id == source_id)
        )

    # Group by passage_id and only keep those that have ALL lemmas
    matching_passage_ids = (
        base_query
        .group_by(LemmaIndex.passage_id)
        .having(func.count(func.distinct(LemmaIndex.lemma)) == len(query_lemmas))
        .subquery()
    )

    # Count total
    total = db.query(func.count()).select_from(matching_passage_ids).scalar()

    # Fetch passages with source info
    results_query = (
        db.query(Passage, Source)
        .join(Source, Source.id == Passage.source_id)
        .filter(Passage.id.in_(db.query(matching_passage_ids)))
        .order_by(Passage.source_id, Passage.start_pos)
        .offset(offset)
        .limit(limit)
    )

    results = []
    for passage, source in results_query:
        # Find match positions within the passage lemmas
        match_positions = []
        if passage.lemmas:
            for i, lemma in enumerate(passage.lemmas):
                if lemma in query_lemmas:
                    match_positions.append(i)

        results.append({
            "passage_id": str(passage.id),
            "text": passage.text,
            "location_label": passage.location_label,
            "source": {
                "id": str(source.id),
                "title": source.title,
                "type": source.type,
            },
            "match_positions": match_positions,
        })

    return {
        "query": query,
        "lemmas": query_lemmas,
        "total": total,
        "results": results,
    }
