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


# ---------------------------------------------------------------------------
# PV filter strategies
# ---------------------------------------------------------------------------

# Blocklist: verb+particle combos that almost always produce FPs because they
# are overwhelmingly used as literal prepositional constructions.
_LITERAL_BLOCKLIST: set[tuple[str, str]] = {
    ("go", "to"),
    ("be", "in"),
    ("be", "on"),
    ("get", "to"),
    ("come", "to"),
    ("have", "in"),
    ("have", "on"),
    ("look", "to"),
}

# High-frequency verbs where dep-parse filtering is most valuable (Option 4).
_HIGH_FREQ_VERBS: set[str] = {
    "go", "be", "get", "come", "have", "look", "take", "make", "do", "put",
}


def has_phrasal_verb_dep(doc, verb_lemma: str, particle_lemmas: list[str]) -> bool:
    """Check if *doc* contains a true phrasal verb via spaCy dependency parse.

    Returns ``True`` when any token whose lemma matches *verb_lemma* has a
    direct child with ``dep_ == "prt"`` whose lemma is in *particle_lemmas*.
    This distinguishes genuine phrasal verbs ("give up") from prepositional
    verbs ("go to Hartford") where the preposition heads a PP complement.
    """
    particle_set = {p.lower() for p in particle_lemmas}
    for token in doc:
        if token.lemma_.lower() == verb_lemma:
            for child in token.children:
                if child.dep_ == "prt" and child.lemma_.lower() in particle_set:
                    return True
    return False


def filter_pv_none(doc, verb_lemma: str, particle_lemmas: list[str]) -> bool:
    """No filtering — accept every lemma match (baseline)."""
    return True


def filter_pv_dep_only(doc, verb_lemma: str, particle_lemmas: list[str]) -> bool:
    """Option 1 (current): require dep_='prt' on particle."""
    return has_phrasal_verb_dep(doc, verb_lemma, particle_lemmas)


def filter_pv_blocklist(doc, verb_lemma: str, particle_lemmas: list[str]) -> bool:
    """Option 2: reject only known FP-generating combos."""
    for p in particle_lemmas:
        if (verb_lemma, p.lower()) in _LITERAL_BLOCKLIST:
            return False
    return True


def filter_pv_dep_extended(doc, verb_lemma: str, particle_lemmas: list[str]) -> bool:
    """Option 3: accept prt OR advmod; for prep, reject if it has a pobj child
    and the verb is high-frequency."""
    particle_set = {p.lower() for p in particle_lemmas}
    for token in doc:
        if token.lemma_.lower() != verb_lemma:
            continue
        for child in token.children:
            if child.lemma_.lower() not in particle_set:
                continue
            if child.dep_ in ("prt", "advmod"):
                return True
            if child.dep_ == "prep":
                has_pobj = any(gc.dep_ == "pobj" for gc in child.children)
                if has_pobj and verb_lemma in _HIGH_FREQ_VERBS:
                    continue  # reject this match, try next
                return True
    return False


def filter_pv_dep_highfreq(doc, verb_lemma: str, particle_lemmas: list[str]) -> bool:
    """Option 4: apply dep_='prt' filter only for high-frequency verbs;
    accept all matches for other verbs."""
    if verb_lemma not in _HIGH_FREQ_VERBS:
        return True
    return has_phrasal_verb_dep(doc, verb_lemma, particle_lemmas)


def filter_pv_hybrid(doc, verb_lemma: str, particle_lemmas: list[str]) -> bool:
    """Option 5 (recommended): accept prt/advmod always, blocklist for prep,
    permissive fallback for everything else."""
    particle_set = {p.lower() for p in particle_lemmas}

    # Check blocklist first — fast rejection
    for p in particle_lemmas:
        if (verb_lemma, p.lower()) in _LITERAL_BLOCKLIST:
            # Even blocklisted combos pass if spaCy sees a true particle
            return has_phrasal_verb_dep(doc, verb_lemma, particle_lemmas)

    # Not blocklisted — accept if dep is prt, advmod, or anything non-prep
    for token in doc:
        if token.lemma_.lower() != verb_lemma:
            continue
        for child in token.children:
            if child.lemma_.lower() in particle_set:
                if child.dep_ in ("prt", "advmod"):
                    return True
                # For non-blocklisted combos, accept even prep
                return True
    # Fallback: no dep relation found between verb and particle
    # (e.g. different parse tree structure) — accept
    return True


PV_FILTERS = {
    "none": filter_pv_none,
    "dep_only": filter_pv_dep_only,
    "blocklist": filter_pv_blocklist,
    "dep_extended": filter_pv_dep_extended,
    "dep_highfreq": filter_pv_dep_highfreq,
    "hybrid": filter_pv_hybrid,
}


def detect_phrasal_verb(query: str) -> dict | None:
    """Check if a query matches a known phrasal verb. Returns info or None."""
    return lookup_phrasal_verb(query)
