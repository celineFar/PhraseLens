"""Idiom search engine.

Detects idioms in user queries and searches the corpus for their occurrences,
handling grammatical variations via lemma-sequence matching.
"""

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Passage, Source
from app.nlp.pipeline import lemmatize_query
from app.search.mwe.lexicon import lookup_idiom, get_idiom_lookup


def search_idiom(
    db: Session,
    query: str,
    source_id: UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search for idiom occurrences in the corpus.

    1. Checks if query matches a known idiom from the lexicon
    2. Searches passages using lemma-sequence matching for variant forms
    3. Returns matches with positions highlighted

    Returns:
        dict with keys: query, idiom, total, results
    """
    # Look up the idiom in our lexicon
    idiom_info = lookup_idiom(query)

    # Get query lemmas for searching
    query_lemmas = lemmatize_query(query)
    if not query_lemmas:
        return {"query": query, "idiom": None, "total": 0, "results": []}

    # Build the passage query - find passages whose lemma list contains
    # all the idiom's lemmas as a subsequence
    base_query = db.query(Passage, Source).join(Source, Source.id == Passage.source_id)

    if source_id:
        base_query = base_query.filter(Passage.source_id == source_id)

    # Filter passages that contain all query lemmas in their lemmas JSONB array
    for lemma in query_lemmas:
        base_query = base_query.filter(Passage.lemmas.op("@>")(f'["{lemma}"]'))

    # Count total matches
    count_query = base_query.with_entities(Passage.id)
    total = count_query.count()

    # Fetch paginated results
    rows = (
        base_query
        .order_by(Passage.source_id, Passage.start_pos)
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for passage, source in rows:
        match_positions = _find_lemma_sequence(passage.lemmas, query_lemmas)

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

    idiom_data = None
    if idiom_info:
        idiom_data = {
            "canonical_form": idiom_info["canonical_form"],
            "definition": idiom_info.get("definition", ""),
            "patterns": idiom_info.get("patterns", []),
        }

    return {
        "query": query,
        "idiom": idiom_data,
        "lemmas": query_lemmas,
        "total": total,
        "results": results,
    }


def _find_lemma_sequence(
    passage_lemmas: list[str] | None,
    query_lemmas: list[str],
) -> list[int]:
    """Find positions where query lemmas appear as a contiguous or near-contiguous sequence.

    Returns positions of each matched lemma in the passage.
    """
    if not passage_lemmas or not query_lemmas:
        return []

    positions = []
    plen = len(passage_lemmas)
    qlen = len(query_lemmas)

    # Sliding window: look for the query lemma sequence within a window
    # that allows up to 2 extra tokens between each query lemma (for articles, etc.)
    for start in range(plen):
        if passage_lemmas[start] == query_lemmas[0]:
            # Try to match the rest of the query lemmas
            matched = [start]
            qi = 1
            pi = start + 1
            gap = 0
            while qi < qlen and pi < plen and gap <= 2:
                if passage_lemmas[pi] == query_lemmas[qi]:
                    matched.append(pi)
                    qi += 1
                    gap = 0
                else:
                    gap += 1
                pi += 1

            if qi == qlen:
                positions.extend(matched)

    return positions


def detect_idiom(query: str) -> dict | None:
    """Check if a query matches a known idiom. Returns idiom info or None."""
    return lookup_idiom(query)
