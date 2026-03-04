import spacy

from app.config import settings

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load(settings.spacy_model)
        except OSError as exc:
            raise RuntimeError(
                "spaCy model "
                f"'{settings.spacy_model}' is not installed.\n"
                "Install it with:\n"
                f"  python -m spacy download {settings.spacy_model}\n"
                "If this environment has no internet access, download the model wheel on"
                " a machine with internet and install it with:\n"
                "  pip install /path/to/en_core_web_sm-<version>-py3-none-any.whl"
            ) from exc
    return _nlp


def tokenize_and_lemmatize(text: str) -> dict:
    """Process text through spaCy and return tokens and lemmas.

    Returns:
        dict with keys:
            - tokens: list of token strings
            - lemmas: list of lemma strings (lowercased)
            - token_lemma_pairs: list of (token, lemma, position) tuples
    """
    nlp = get_nlp()
    doc = nlp(text)

    tokens = []
    lemmas = []
    pairs = []

    for i, token in enumerate(doc):
        if token.is_space:
            continue
        tokens.append(token.text)
        lemma = token.lemma_.lower()
        lemmas.append(lemma)
        pairs.append({"token": token.text, "lemma": lemma, "pos": i})

    return {
        "tokens": tokens,
        "lemmas": lemmas,
        "token_lemma_pairs": pairs,
    }


def lemmatize_query(query: str) -> list[str]:
    """Lemmatize a search query, returning only content word lemmas (no punct/space)."""
    nlp = get_nlp()
    doc = nlp(query)
    return [
        token.lemma_.lower()
        for token in doc
        if not token.is_space and not token.is_punct
    ]
