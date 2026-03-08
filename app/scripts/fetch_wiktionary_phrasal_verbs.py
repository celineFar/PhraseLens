#!/usr/bin/env python3
"""Fetch English phrasal verbs from Wiktionary category members API.

Writes a compact JSON file under data/lexicons that can be merged into the
existing phrasal-verb lexicon as a supplemental source.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://en.wiktionary.org/w/api.php"
CATEGORY_TITLE = "Category:English_phrasal_verbs"


def _fetch_page(cmcontinue: str | None = None) -> dict:
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": CATEGORY_TITLE,
        "cmlimit": "500",
        "format": "json",
    }
    if cmcontinue:
        params["cmcontinue"] = cmcontinue
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PhraseLensLexiconBot/1.0 (research integration)",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _normalize_phrase(phrase: str) -> str:
    phrase = phrase.strip().lower()
    phrase = re.sub(r"\s+", " ", phrase)
    return phrase


def _is_reasonable_pv_title(title: str) -> bool:
    # Keep multiword expressions; drop unusual namespace-like leftovers.
    if " " not in title:
        return False
    return ":" not in title


def fetch_all_titles() -> list[str]:
    titles: list[str] = []
    cmcontinue: str | None = None
    while True:
        page = _fetch_page(cmcontinue=cmcontinue)
        members = page.get("query", {}).get("categorymembers", [])
        for m in members:
            t = _normalize_phrase(m.get("title", ""))
            if t and _is_reasonable_pv_title(t):
                titles.append(t)
        cmcontinue = page.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
    return sorted(set(titles))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="data/lexicons/phrasal_verbs_wiktionary_category.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    phrases = fetch_all_titles()
    payload = {
        "source": "Wiktionary Category:English_phrasal_verbs via MediaWiki API",
        "source_url": (
            "https://en.wiktionary.org/w/api.php?action=query&list=categorymembers"
            "&cmtitle=Category:English_phrasal_verbs&cmlimit=max&format=json"
        ),
        "license": "CC BY-SA 3.0 (Wiktionary/Wikimedia terms apply)",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(phrases),
        "phrases": phrases,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Wrote {len(phrases)} entries to {out}")


if __name__ == "__main__":
    main()
