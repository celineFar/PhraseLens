#!/usr/bin/env python3
"""Build phrasal-verb supplement from external DiMSUM and PARSEME datasets.

Output format is compatible with existing wecan-like JSON maps:
{ "<phrase>": { "derivatives": [], "descriptions": [], "examples": [] } }
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def _norm_phrase(lemmas: list[str]) -> str:
    phrase = " ".join((x or "").strip().lower() for x in lemmas if x)
    phrase = re.sub(r"\s+", " ", phrase).strip()
    return phrase


def _is_candidate(upos: list[str], lemmas: list[str]) -> bool:
    if len(lemmas) < 2 or len(lemmas) > 6:
        return False
    if not upos or upos[0] not in {"VERB", "AUX"}:
        return False
    if any(not re.search(r"[a-z]", l or "", re.I) for l in lemmas):
        return False
    return True


def _extract_dimsum_phrases(path: Path) -> list[str]:
    phrases: list[str] = []
    sent: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                if sent:
                    phrases.extend(_extract_dimsum_sentence_mwes(sent))
                    sent = []
                continue
            cols = line.split("\t")
            if len(cols) < 6:
                continue
            sent.append({
                "id": int(cols[0]),
                "lemma": cols[2].lower(),
                "upos": cols[3],
                "tag": cols[4],
                "parent": int(cols[5]) if cols[5].isdigit() else 0,
            })
    if sent:
        phrases.extend(_extract_dimsum_sentence_mwes(sent))
    return phrases


def _extract_dimsum_sentence_mwes(sent: list[dict]) -> list[str]:
    by_id = {t["id"]: t for t in sent}

    def root_id(tok_id: int) -> int:
        seen = set()
        cur = tok_id
        while cur in by_id and cur not in seen:
            seen.add(cur)
            t = by_id[cur]
            if t["tag"] == "B":
                return cur
            parent = t["parent"]
            if parent <= 0:
                return tok_id
            cur = parent
        return tok_id

    groups: dict[int, list[dict]] = defaultdict(list)
    for t in sent:
        if t["tag"] not in {"B", "I"}:
            continue
        groups[root_id(t["id"])].append(t)

    out: list[str] = []
    for toks in groups.values():
        toks = sorted(toks, key=lambda x: x["id"])
        lemmas = [t["lemma"] for t in toks]
        upos = [t["upos"] for t in toks]
        if not _is_candidate(upos, lemmas):
            continue
        phrase = _norm_phrase(lemmas)
        if phrase:
            out.append(phrase)
    return out


def _parse_cupt_sentence_mwes(sent: list[dict]) -> list[tuple[list[str], list[str], str]]:
    groups: dict[str, dict] = defaultdict(lambda: {"toks": [], "cat": ""})
    for tok in sent:
        tag = tok["mwe"]
        if tag in {"*", "_", ""}:
            continue
        for part in tag.split(";"):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                mwe_id, cat = part.split(":", 1)
            else:
                mwe_id, cat = part, ""
            groups[mwe_id]["toks"].append(tok)
            if cat and not groups[mwe_id]["cat"]:
                groups[mwe_id]["cat"] = cat

    out: list[tuple[list[str], list[str], str]] = []
    for item in groups.values():
        toks = sorted(item["toks"], key=lambda x: x["id"])
        lemmas = [t["lemma"] for t in toks]
        upos = [t["upos"] for t in toks]
        out.append((lemmas, upos, item["cat"]))
    return out


def _read_cupt(path: Path) -> list[list[dict]]:
    sents: list[list[dict]] = []
    sent: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                if sent:
                    sents.append(sent)
                    sent = []
                continue
            if line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) < 11:
                continue
            tok_id = cols[0]
            if "-" in tok_id or "." in tok_id:
                continue
            if not tok_id.isdigit():
                continue
            sent.append({
                "id": int(tok_id),
                "lemma": cols[2].lower(),
                "upos": cols[3],
                "mwe": cols[10],
            })
    if sent:
        sents.append(sent)
    return sents


def _parseme_english_files(root: Path) -> list[Path]:
    files = []
    patterns = [
        "1.1/EN/*.cupt",
        "1.1/trial/*.cupt",
        "1.2/trial/*.cupt",
        "2.0/subtask1_trial/EN/*.cupt",
    ]
    for pat in patterns:
        files.extend(root.glob(pat))
    keep: list[Path] = []
    for p in files:
        name = p.name.lower()
        if "blind" in name or "pred" in name or "system" in name:
            continue
        keep.append(p)
    return sorted(set(keep))


def build_supplement(external_root: Path) -> tuple[dict, dict]:
    sources = defaultdict(int)
    parseme_cats: dict[str, set[str]] = defaultdict(set)
    phrase_sources: dict[str, set[str]] = defaultdict(set)

    dimsum_train = external_root / "dimsum" / "dimsum16-dimsum-data-cd92971" / "dimsum16.train"
    if dimsum_train.exists():
        for ph in _extract_dimsum_phrases(dimsum_train):
            sources["dimsum_mwe_instances"] += 1
            phrase_sources[ph].add("dimsum")

    parseme_root = external_root / "parseme" / "sharedtask-data-master"
    for cupt in _parseme_english_files(parseme_root):
        for sent in _read_cupt(cupt):
            for lemmas, upos, cat in _parse_cupt_sentence_mwes(sent):
                if not _is_candidate(upos, lemmas):
                    continue
                ph = _norm_phrase(lemmas)
                if not ph:
                    continue
                sources["parseme_mwe_instances"] += 1
                phrase_sources[ph].add("parseme")
                if cat:
                    parseme_cats[ph].add(cat)

    out: dict[str, dict] = {}
    for phrase, srcs in phrase_sources.items():
        desc = [f"External MWE candidate from {'+'.join(sorted(srcs))}"]
        cats = sorted(parseme_cats.get(phrase, set()))
        if cats:
            desc.append(f"PARSEME categories: {', '.join(cats)}")
        out[phrase] = {
            "derivatives": [],
            "descriptions": desc,
            "examples": [],
            "frequency": 0,
            "sources": sorted(srcs),
            "parseme_categories": cats,
        }
    sources["unique_phrases"] = len(out)
    return out, dict(sources)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--external-root",
        default="data/external",
        help="Root directory containing extracted external datasets",
    )
    parser.add_argument(
        "--output",
        default="data/lexicons/phrasal_verbs_external_mwe.json",
        help="Output JSON file",
    )
    args = parser.parse_args()

    payload, stats = build_supplement(Path(args.external_root))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload)} phrases to {out_path}")
    print("Stats:", stats)


if __name__ == "__main__":
    main()
