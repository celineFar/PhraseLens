"""Lexicon loader for idioms and phrasal verbs.

Loads JSON lexicon files lazily and provides lookup functions.
Uses normalized text keys (not lemmatization) for fast startup.
"""

import json
import logging
import os
import re

from app.config import settings
from app.nlp.pipeline import get_nlp

logger = logging.getLogger(__name__)

_idiom_lookup: dict[str, dict] | None = None
_phrasal_verbs: dict[str, dict] | None = None


def _normalize_key(phrase: str) -> str:
    """Normalize a phrase to a lowercase key with only alphanumeric + spaces."""
    return re.sub(r"[^a-z0-9 ]", "", phrase.lower()).strip()


def _normalize_key_lemma(phrase: str) -> str:
    """Lemmatize and normalize a phrase for lookup."""
    nlp = get_nlp()
    doc = nlp(phrase)
    return " ".join(
        token.lemma_.lower()
        for token in doc
        if not token.is_space and not token.is_punct
    )


def _load_idioms() -> dict[str, dict]:
    """Load idioms from McGraw Hill JSON with text-normalized keys.

    Instead of lemmatizing all 21K+ phrases at load time, we index by
    normalized text and also by each pattern variant.
    """
    lexicon_path = os.path.join(settings.data_dir, "lexicons", "idioms_mcgrawhill.json")
    if not os.path.exists(lexicon_path):
        logger.warning("Idiom lexicon not found at %s", lexicon_path)
        return {}

    with open(lexicon_path, "r") as f:
        raw = json.load(f)

    entries = raw.get("dictionary", [])
    lookup: dict[str, dict] = {}

    for entry in entries:
        phrase = entry.get("phrase", "")
        if not phrase:
            continue

        patterns = entry.get("patterns", [phrase])
        definition = entry.get("definition", "")
        definition = re.sub(r"[_]", "", definition).strip()

        idiom_entry = {
            "canonical_form": phrase,
            "patterns": patterns,
            "definition": definition,
        }

        # Index by normalized phrase and each pattern
        lookup[_normalize_key(phrase)] = idiom_entry
        for p in patterns:
            lookup[_normalize_key(p)] = idiom_entry

    # Build lemmatized keys so lemma fallback works for plurals etc.
    nlp = get_nlp()
    lemma_additions: dict[str, dict] = {}
    for entry in entries:
        phrase = entry.get("phrase", "")
        if not phrase:
            continue
        doc = nlp(phrase)
        lemma_key = " ".join(
            t.lemma_.lower() for t in doc if not t.is_space and not t.is_punct
        )
        if lemma_key and lemma_key not in lookup:
            lemma_additions[lemma_key] = lookup.get(_normalize_key(phrase), {})
    lookup.update(lemma_additions)

    logger.info("Loaded %d idioms (%d lookup keys)", len(entries), len(lookup))
    return lookup


def _parse_phrasal_verb_entry(verb_field: str) -> tuple[str, str, bool]:
    """Parse verb field like 'blow * up +' into (verb, particle, separable)."""
    clean = verb_field.replace("+", "").strip()
    separable = "*" in clean
    clean = clean.replace("*", "").strip()
    parts = clean.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:]), separable
    return clean, "", False


def _load_phrasal_verbs() -> dict[str, dict]:
    """Load phrasal verbs from both lexicon sources and merge."""
    pv_dict: dict[str, dict] = {}

    # Load wecan (larger, 3350 entries with derivatives)
    wecan_path = os.path.join(settings.data_dir, "lexicons", "phrasal_verbs_wecan.json")
    if os.path.exists(wecan_path):
        with open(wecan_path, "r") as f:
            wecan = json.load(f)
        for phrase, data in wecan.items():
            parts = phrase.split()
            if len(parts) >= 2:
                verb = parts[0]
                particle = " ".join(parts[1:])
            else:
                verb, particle = phrase, ""

            pv_dict[phrase] = {
                "verb": verb,
                "particle": particle,
                "separable": False,
                "derivatives": data.get("derivatives", []),
                "definition": "; ".join(data.get("descriptions", [])),
                "examples": data.get("examples", []),
            }
        logger.info("Loaded %d phrasal verbs from wecan", len(wecan))

    # Load semigradsky (smaller, 124 entries with separability info)
    semi_path = os.path.join(settings.data_dir, "lexicons", "phrasal_verbs_semigradsky.json")
    if os.path.exists(semi_path):
        with open(semi_path, "r") as f:
            semi = json.load(f)
        for entry in semi:
            verb_field = entry.get("verb", "")
            verb, particle, separable = _parse_phrasal_verb_entry(verb_field)
            canonical = f"{verb} {particle}".strip()

            if canonical in pv_dict:
                pv_dict[canonical]["separable"] = separable
            else:
                pv_dict[canonical] = {
                    "verb": verb,
                    "particle": particle,
                    "separable": separable,
                    "derivatives": [],
                    "definition": entry.get("definition", ""),
                    "examples": entry.get("examples", []),
                }
        logger.info("Loaded/merged %d phrasal verbs from semigradsky", len(semi))

    # Build lemma-based keys for lookup
    nlp = get_nlp()
    for pv in pv_dict.values():
        verb_doc = nlp(pv["verb"])
        verb_lemma = verb_doc[0].lemma_.lower() if verb_doc else pv["verb"]
        pv["verb_lemma"] = verb_lemma
        # Lemmatize particle tokens too (e.g., "going" -> "go")
        particle_doc = nlp(pv["particle"]) if pv["particle"] else []
        particle_lemmas = [t.lemma_.lower() for t in particle_doc
                          if not t.is_space and not t.is_punct]
        pv["particle_lemmas"] = particle_lemmas or pv["particle"].split()
        pv["search_lemmas"] = [verb_lemma] + pv["particle_lemmas"]
        pv["lemma_key"] = " ".join(pv["search_lemmas"])

    logger.info("Total phrasal verbs loaded: %d", len(pv_dict))
    return pv_dict


def get_idiom_lookup() -> dict[str, dict]:
    """Get idiom lookup dict keyed by normalized text."""
    global _idiom_lookup
    if _idiom_lookup is None:
        _idiom_lookup = _load_idioms()
    return _idiom_lookup


def get_phrasal_verbs() -> dict[str, dict]:
    """Get all loaded phrasal verbs keyed by canonical form."""
    global _phrasal_verbs
    if _phrasal_verbs is None:
        _phrasal_verbs = _load_phrasal_verbs()
    return _phrasal_verbs


def lookup_idiom(query: str) -> dict | None:
    """Look up an idiom by normalized text, lemmatized form, or subsequence match."""
    lookup = get_idiom_lookup()

    # Fast path: direct normalized text match
    normalized = _normalize_key(query)
    if normalized in lookup:
        return lookup[normalized]

    # Slow path: lemmatize query and search
    lemma_key = _normalize_key_lemma(query)
    if lemma_key in lookup:
        return lookup[lemma_key]

    # Tolerant path: check if any idiom's lemmas are a subsequence of query lemmas
    query_lemmas = lemma_key.split()
    if len(query_lemmas) >= 3:
        nlp = get_nlp()
        best_match = None
        best_len = 0
        for key, entry in lookup.items():
            idiom_tokens = key.split()
            if len(idiom_tokens) < 2 or len(idiom_tokens) > len(query_lemmas):
                continue
            if len(idiom_tokens) <= best_len:
                continue
            if _is_subsequence(idiom_tokens, query_lemmas):
                best_match = entry
                best_len = len(idiom_tokens)
        if best_match is not None:
            return best_match

    return None


def _is_subsequence(subseq: list[str], seq: list[str]) -> bool:
    """Check if subseq appears as a subsequence in seq (preserving order)."""
    it = iter(seq)
    return all(token in it for token in subseq)


_OBJECT_PRONOUNS = {"it", "them", "him", "her", "me", "us", "you", "this", "that"}


def lookup_phrasal_verb(query: str) -> dict | None:
    """Look up a phrasal verb by its canonical or lemmatized form."""
    pvs = get_phrasal_verbs()

    # Direct lookup
    query_lower = query.lower().strip()
    if query_lower in pvs:
        return pvs[query_lower]

    # Lemma-based lookup
    lemma_query = _normalize_key_lemma(query)
    for pv in pvs.values():
        if pv.get("lemma_key") == lemma_query:
            return pv

    # Strip object pronouns and retry (e.g. "turned it off" -> "turned off")
    words = query_lower.split()
    stripped = [w for w in words if w not in _OBJECT_PRONOUNS]
    if len(stripped) != len(words) and len(stripped) >= 2:
        stripped_query = " ".join(stripped)
        if stripped_query in pvs:
            return pvs[stripped_query]
        stripped_lemma = _normalize_key_lemma(stripped_query)
        for pv in pvs.values():
            if pv.get("lemma_key") == stripped_lemma:
                return pv

    return None
