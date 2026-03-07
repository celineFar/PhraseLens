"""Collocation search engine.

Computes co-occurrence statistics (PMI) from the corpus and provides
collocation lookup and search functionality.
"""

import math
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Passage, Source, LemmaIndex
from app.nlp.pipeline import lemmatize_query


def get_collocations(
    db: Session,
    word: str,
    limit: int = 20,
) -> dict:
    """Get top collocates for a target word, ranked by PMI score.

    Computes collocations on-the-fly from the LemmaIndex:
    1. Find all passages containing the target lemma
    2. Count co-occurring lemmas in those passages
    3. Compute PMI for each co-occurring lemma
    4. Return top collocates ranked by PMI

    Returns:
        dict with keys: word, lemma, total, collocations
    """
    query_lemmas = lemmatize_query(word)
    if not query_lemmas:
        return {"word": word, "lemma": None, "total": 0, "collocations": []}

    target_lemma = query_lemmas[0]

    # Count total passages in corpus
    total_passages = db.query(func.count(Passage.id)).scalar() or 1

    # Find passages containing the target lemma
    target_passage_ids = (
        db.query(LemmaIndex.passage_id)
        .filter(LemmaIndex.lemma == target_lemma)
        .subquery()
    )
    target_count = (
        db.query(func.count())
        .select_from(target_passage_ids)
        .scalar()
    ) or 0

    if target_count == 0:
        return {
            "word": word,
            "lemma": target_lemma,
            "total": 0,
            "collocations": [],
        }

    # Find co-occurring lemmas and their counts
    cooccurrences = (
        db.query(
            LemmaIndex.lemma,
            func.count(func.distinct(LemmaIndex.passage_id)).label("cooccur_count"),
        )
        .filter(LemmaIndex.passage_id.in_(db.query(target_passage_ids)))
        .filter(LemmaIndex.lemma != target_lemma)
        # Skip very short or common function words
        .filter(func.length(LemmaIndex.lemma) > 1)
        .group_by(LemmaIndex.lemma)
        .having(func.count(func.distinct(LemmaIndex.passage_id)) >= 2)
        .all()
    )

    # Compute PMI for each co-occurring lemma
    # PMI = log2(P(x,y) / (P(x) * P(y)))
    # P(x,y) = cooccur_count / total_passages
    # P(x) = target_count / total_passages
    # P(y) = lemma_count / total_passages
    collocations = []
    p_target = target_count / total_passages

    # Batch-fetch the corpus frequency of each co-occurring lemma
    cooccur_lemmas = [lemma for lemma, _ in cooccurrences]
    if cooccur_lemmas:
        lemma_counts = dict(
            db.query(
                LemmaIndex.lemma,
                func.count(func.distinct(LemmaIndex.passage_id)),
            )
            .filter(LemmaIndex.lemma.in_(cooccur_lemmas))
            .group_by(LemmaIndex.lemma)
            .all()
        )
    else:
        lemma_counts = {}

    for lemma, cooccur_count in cooccurrences:
        lemma_total = lemma_counts.get(lemma, 1)
        p_lemma = lemma_total / total_passages
        p_cooccur = cooccur_count / total_passages

        pmi = math.log2(p_cooccur / (p_target * p_lemma)) if (p_target * p_lemma) > 0 else 0

        collocations.append({
            "word": lemma,
            "frequency": cooccur_count,
            "pmi": round(pmi, 4),
        })

    # Sort by PMI descending, then by frequency
    collocations.sort(key=lambda x: (-x["pmi"], -x["frequency"]))
    collocations = collocations[:limit]

    return {
        "word": word,
        "lemma": target_lemma,
        "target_frequency": target_count,
        "total": len(collocations),
        "collocations": collocations,
    }


def search_collocation(
    db: Session,
    word1: str,
    word2: str,
    source_id: UUID | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search for occurrences of a specific word pair (collocation) in the corpus.

    Returns:
        dict with keys: query, lemmas, total, results
    """
    lemmas1 = lemmatize_query(word1)
    lemmas2 = lemmatize_query(word2)

    if not lemmas1 or not lemmas2:
        return {"query": f"{word1} {word2}", "lemmas": [], "total": 0, "results": []}

    search_lemmas = [lemmas1[0], lemmas2[0]]

    base_query = db.query(Passage, Source).join(Source, Source.id == Passage.source_id)

    if source_id:
        base_query = base_query.filter(Passage.source_id == source_id)

    for lemma in search_lemmas:
        base_query = base_query.filter(Passage.lemmas.op("@>")(f'["{lemma}"]'))

    total = base_query.with_entities(Passage.id).count()

    rows = (
        base_query
        .order_by(Passage.source_id, Passage.start_pos)
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for passage, source in rows:
        match_positions = []
        if passage.lemmas:
            for i, lemma in enumerate(passage.lemmas):
                if lemma in search_lemmas:
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
        "query": f"{word1} {word2}",
        "lemmas": search_lemmas,
        "total": total,
        "results": results,
    }
