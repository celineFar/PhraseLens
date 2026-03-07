"""Phrasal verb search engine.

Detects phrasal verbs in user queries and searches the corpus for their
occurrences, handling particle separation and verb conjugation.
"""

import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Passage, Source
from app.nlp.pipeline import lemmatize_query
from app.search.mwe.lexicon import lookup_phrasal_verb


def search_phrasal_verb(
    db: Session,
    query: str,
    source_id: UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search for phrasal verb occurrences in the corpus.

    Handles both contiguous ("give up") and separated ("give it up") forms.

    Returns:
        dict with keys: query, phrasal_verb, total, results
    """
    pv_info = lookup_phrasal_verb(query)

    query_lemmas = lemmatize_query(query)
    if not query_lemmas:
        return {"query": query, "phrasal_verb": None, "total": 0, "results": []}

    # For phrasal verbs, we need the verb lemma + particle lemmas
    if pv_info:
        search_lemmas = pv_info.get("search_lemmas") or (
            [pv_info["verb_lemma"]] + pv_info["particle"].split()
        )
    else:
        search_lemmas = query_lemmas

    # Find passages containing all the required lemmas
    base_query = db.query(Passage, Source).join(Source, Source.id == Passage.source_id)

    if source_id:
        base_query = base_query.filter(Passage.source_id == source_id)

    for lemma in search_lemmas:
        base_query = base_query.filter(Passage.lemmas.op("@>")(f'["{lemma}"]'))

    count_query = base_query.with_entities(Passage.id)
    total = count_query.count()

    rows = (
        base_query
        .order_by(Passage.source_id, Passage.start_pos)
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Determine max separation gap for particle
    # Separable phrasal verbs can have objects between verb and particle
    max_gap = 6 if (pv_info and pv_info.get("separable")) else 1

    results = []
    for passage, source in rows:
        match_positions = _find_phrasal_verb_positions(
            passage.lemmas, search_lemmas, max_gap=max_gap
        )

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

    pv_data = None
    if pv_info:
        pv_data = {
            "verb": pv_info["verb"],
            "particle": pv_info["particle"],
            "separable": pv_info.get("separable", False),
            "definition": pv_info.get("definition", ""),
        }

    return {
        "query": query,
        "phrasal_verb": pv_data,
        "lemmas": search_lemmas,
        "total": total,
        "results": results,
    }


def _find_phrasal_verb_positions(
    passage_lemmas: list[str] | None,
    search_lemmas: list[str],
    max_gap: int = 3,
) -> list[int]:
    """Find positions of phrasal verb components in passage lemmas.

    Allows a gap of up to max_gap tokens between verb and particle
    to handle separated phrasal verbs (e.g., "turn the lights off").
    """
    if not passage_lemmas or not search_lemmas:
        return []

    positions = []
    plen = len(passage_lemmas)

    for start in range(plen):
        if passage_lemmas[start] == search_lemmas[0]:
            matched = [start]
            qi = 1
            pi = start + 1
            gap = 0
            while qi < len(search_lemmas) and pi < plen and gap <= max_gap:
                if passage_lemmas[pi] == search_lemmas[qi]:
                    matched.append(pi)
                    qi += 1
                    gap = 0
                else:
                    gap += 1
                pi += 1

            if qi == len(search_lemmas):
                positions.extend(matched)

    return positions


def detect_phrasal_verb(query: str) -> dict | None:
    """Check if a query matches a known phrasal verb. Returns info or None."""
    return lookup_phrasal_verb(query)
