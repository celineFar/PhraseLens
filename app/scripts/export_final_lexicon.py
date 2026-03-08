#!/usr/bin/env python3
"""Export the current merged lexicon to downloadable files (JSONL/CSV/ZIP)."""

from __future__ import annotations

import csv
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def _parse_semigradsky_verb_field(verb_field: str) -> tuple[str, str, bool]:
    clean = verb_field.replace("+", "").strip()
    separable = "*" in clean
    clean = clean.replace("*", "").strip()
    parts = clean.split()
    if len(parts) >= 2:
        return parts[0], " ".join(parts[1:]), separable
    return clean, "", False


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    lex = root / "data" / "lexicons"
    out_dir = root / "data" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    idioms_raw = json.loads((lex / "idioms_mcgrawhill.json").read_text(encoding="utf-8"))["dictionary"]
    wecan = json.loads((lex / "phrasal_verbs_wecan.json").read_text(encoding="utf-8"))
    semigradsky = json.loads((lex / "phrasal_verbs_semigradsky.json").read_text(encoding="utf-8"))
    wiki_payload = json.loads((lex / "phrasal_verbs_wiktionary_category.json").read_text(encoding="utf-8"))
    wiki_phrases = wiki_payload.get("phrases", [])
    external = {}
    external_path = lex / "phrasal_verbs_external_mwe.json"
    if external_path.exists():
        external = json.loads(external_path.read_text(encoding="utf-8"))

    rows: list[dict] = []

    # Idioms
    for e in idioms_raw:
        phrase = (e.get("phrase") or "").strip()
        if not phrase:
            continue
        definition = re.sub(r"[_]", "", e.get("definition", "")).strip()
        patterns = e.get("patterns", []) or []
        rows.append({
            "type": "idiom",
            "canonical": phrase,
            "definition": definition,
            "separable": "",
            "sources": "idioms_mcgrawhill",
            "patterns_count": len(patterns),
            "derivatives_count": 0,
            "examples_count": 0,
        })

    # Phrasal verbs merge
    pv: dict[str, dict] = {}
    for phrase, data in wecan.items():
        parts = phrase.split()
        if len(parts) < 2:
            continue
        pv[phrase] = {
            "definition": "; ".join(data.get("descriptions", [])),
            "separable": False,
            "sources": {"wecan"},
            "derivatives_count": len(data.get("derivatives", []) or []),
            "examples_count": len(data.get("examples", []) or []),
        }

    for entry in semigradsky:
        verb, particle, separable = _parse_semigradsky_verb_field(entry.get("verb", ""))
        canonical = f"{verb} {particle}".strip()
        if not canonical or len(canonical.split()) < 2:
            continue
        if canonical in pv:
            pv[canonical]["separable"] = separable
            pv[canonical]["sources"].add("semigradsky")
            if not pv[canonical]["definition"]:
                pv[canonical]["definition"] = entry.get("definition", "")
        else:
            pv[canonical] = {
                "definition": entry.get("definition", ""),
                "separable": separable,
                "sources": {"semigradsky"},
                "derivatives_count": 0,
                "examples_count": len(entry.get("examples", []) or []),
            }

    for phrase, data in external.items():
        canonical = phrase.strip().lower()
        if not canonical or len(canonical.split()) < 2:
            continue
        if canonical in pv:
            pv[canonical]["sources"].add("external_mwe")
            continue
        pv[canonical] = {
            "definition": "; ".join(data.get("descriptions", [])),
            "separable": False,
            "sources": {"external_mwe"},
            "derivatives_count": len(data.get("derivatives", []) or []),
            "examples_count": len(data.get("examples", []) or []),
        }

    for phrase in wiki_phrases:
        canonical = phrase.strip().lower()
        if not canonical or len(canonical.split()) < 2:
            continue
        if canonical in pv:
            pv[canonical]["sources"].add("wiktionary_category")
            continue
        pv[canonical] = {
            "definition": "",
            "separable": False,
            "sources": {"wiktionary_category"},
            "derivatives_count": 0,
            "examples_count": 0,
        }

    for canonical, data in pv.items():
        rows.append({
            "type": "phrasal_verb",
            "canonical": canonical,
            "definition": data["definition"],
            "separable": str(bool(data["separable"])).lower(),
            "sources": "|".join(sorted(data["sources"])),
            "patterns_count": 0,
            "derivatives_count": data["derivatives_count"],
            "examples_count": data["examples_count"],
        })

    rows.sort(key=lambda r: (r["type"], r["canonical"]))

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = f"final_lexicon_export_{ts}"
    jsonl_path = out_dir / f"{base}.jsonl"
    csv_path = out_dir / f"{base}.csv"
    meta_path = out_dir / f"{base}.meta.json"
    zip_path = out_dir / f"{base}.zip"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=True) + "\n")

    fieldnames = [
        "type",
        "canonical",
        "definition",
        "separable",
        "sources",
        "patterns_count",
        "derivatives_count",
        "examples_count",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    meta = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_entries": len(rows),
        "idiom_entries": sum(1 for r in rows if r["type"] == "idiom"),
        "phrasal_verb_entries": sum(1 for r in rows if r["type"] == "phrasal_verb"),
        "inputs": [
            "idioms_mcgrawhill.json",
            "phrasal_verbs_wecan.json",
            "phrasal_verbs_semigradsky.json",
            "phrasal_verbs_external_mwe.json (if present)",
            "phrasal_verbs_wiktionary_category.json",
        ],
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=True, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(jsonl_path, arcname=jsonl_path.name)
        z.write(csv_path, arcname=csv_path.name)
        z.write(meta_path, arcname=meta_path.name)

    print("Created:")
    print(jsonl_path)
    print(csv_path)
    print(meta_path)
    print(zip_path)
    print("Summary:", meta)


if __name__ == "__main__":
    main()
