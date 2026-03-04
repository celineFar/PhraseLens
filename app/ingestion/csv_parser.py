"""Parsers for each CSV format, normalizing into a unified line structure."""

import re
from dataclasses import dataclass

import pandas as pd


@dataclass
class TranscriptLine:
    season: str
    episode: str
    episode_title: str
    speaker: str
    text: str
    line_order: int


# Registry mapping filename patterns to parser functions
SHOW_REGISTRY = {
    "The-Office": {
        "title": "The Office",
        "parser": "parse_office",
    },
    "friends_quotes": {
        "title": "Friends",
        "parser": "parse_friends",
    },
    "Gilmore_Girls": {
        "title": "Gilmore Girls",
        "parser": "parse_gilmore_girls",
    },
    "1_10_seasons_tbbt": {
        "title": "The Big Bang Theory",
        "parser": "parse_tbbt",
    },
    "himym_full_transcripts": {
        "title": "How I Met Your Mother",
        "parser": "parse_himym",
    },
}


def identify_show(filename: str) -> dict | None:
    """Match a filename to a show in the registry."""
    for key, info in SHOW_REGISTRY.items():
        if key in filename:
            return info
    return None


def parse_office(filepath: str) -> list[TranscriptLine]:
    df = pd.read_csv(filepath)
    lines = []
    for i, row in df.iterrows():
        text = str(row.get("line", "")).strip()
        if not text or text == "nan":
            continue
        lines.append(TranscriptLine(
            season=str(int(row["season"])),
            episode=str(int(row["episode"])),
            episode_title=str(row.get("title", "")),
            speaker=str(row.get("speaker", "")).strip(),
            text=text,
            line_order=i,
        ))
    return lines


def parse_friends(filepath: str) -> list[TranscriptLine]:
    df = pd.read_csv(filepath)
    lines = []
    for i, row in df.iterrows():
        text = str(row.get("quote", "")).strip()
        if not text or text == "nan":
            continue
        season = str(int(row["season"])) if pd.notna(row.get("season")) else ""
        episode = str(int(row["episode_number"])) if pd.notna(row.get("episode_number")) else ""
        lines.append(TranscriptLine(
            season=season,
            episode=episode,
            episode_title=str(row.get("episode_title", "")),
            speaker=str(row.get("author", "")).strip(),
            text=text,
            line_order=i,
        ))
    return lines


def parse_gilmore_girls(filepath: str) -> list[TranscriptLine]:
    df = pd.read_csv(filepath)
    lines = []
    for i, row in df.iterrows():
        text = str(row.get("Line", "")).strip()
        if not text or text == "nan":
            continue
        season = str(int(row["Season"])) if pd.notna(row.get("Season")) else ""
        lines.append(TranscriptLine(
            season=season,
            episode="",
            episode_title="",
            speaker=str(row.get("Character", "")).strip(),
            text=text,
            line_order=i,
        ))
    return lines


def parse_tbbt(filepath: str) -> list[TranscriptLine]:
    df = pd.read_csv(filepath)
    lines = []
    for i, row in df.iterrows():
        text = str(row.get("dialogue", "")).strip()
        if not text or text == "nan":
            continue

        person = str(row.get("person_scene", "")).strip()
        # Skip scene descriptions
        if person == "Scene":
            continue

        ep_name = str(row.get("episode_name", ""))
        # Parse "Series 01 Episode 01 – Title"
        match = re.match(r"Series\s+(\d+)\s+Episode\s+(\d+)\s*[–-]\s*(.*)", ep_name)
        if match:
            season, episode, title = match.group(1), match.group(2), match.group(3)
        else:
            season, episode, title = "", "", ep_name

        lines.append(TranscriptLine(
            season=season.lstrip("0") or "0",
            episode=episode.lstrip("0") or "0",
            episode_title=title.strip(),
            speaker=person,
            text=text,
            line_order=i,
        ))
    return lines


def parse_himym(filepath: str) -> list[TranscriptLine]:
    df = pd.read_csv(filepath)
    lines = []
    for i, row in df.iterrows():
        text = str(row.get("line", "")).strip()
        if not text or text == "nan":
            continue

        ep_str = str(row.get("episode", ""))
        # Parse "4x02 - Title"
        match = re.match(r"(\d+)x(\d+)\s*-\s*(.*)", ep_str)
        if match:
            season, episode, title = match.group(1), match.group(2), match.group(3)
        else:
            season, episode, title = "", "", ep_str

        lines.append(TranscriptLine(
            season=season,
            episode=episode.lstrip("0") or "0",
            episode_title=title.strip(),
            speaker=str(row.get("name", "")).strip(),
            text=text,
            line_order=i,
        ))
    return lines


# Dispatch table
PARSERS = {
    "parse_office": parse_office,
    "parse_friends": parse_friends,
    "parse_gilmore_girls": parse_gilmore_girls,
    "parse_tbbt": parse_tbbt,
    "parse_himym": parse_himym,
}


def parse_csv(filepath: str) -> tuple[str, list[TranscriptLine]]:
    """Auto-detect show from filename and parse the CSV.

    Returns:
        (show_title, list of TranscriptLine)
    """
    import os
    filename = os.path.basename(filepath)
    show_info = identify_show(filename)
    if show_info is None:
        raise ValueError(f"Unknown CSV format: {filename}")

    parser_fn = PARSERS[show_info["parser"]]
    return show_info["title"], parser_fn(filepath)
