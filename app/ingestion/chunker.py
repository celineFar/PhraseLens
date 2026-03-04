"""Group transcript lines into passages, respecting episode boundaries."""

from app.ingestion.csv_parser import TranscriptLine


def chunk_lines(lines: list[TranscriptLine], chunk_size: int = 5) -> list[dict]:
    """Group consecutive lines into passages.

    Lines are grouped by (season, episode). Each passage contains up to
    `chunk_size` lines. Returns a list of passage dicts ready for DB insertion.

    Returns:
        list of dicts with keys: text, location_label, start_pos, end_pos, lines
    """
    if not lines:
        return []

    passages = []
    current_key = None
    current_chunk: list[TranscriptLine] = []

    for line in lines:
        line_key = (line.season, line.episode)

        # Flush on episode boundary or chunk full
        if line_key != current_key or len(current_chunk) >= chunk_size:
            if current_chunk:
                passages.append(_build_passage(current_chunk))
            current_chunk = []
            current_key = line_key

        current_chunk.append(line)

    # Flush remaining
    if current_chunk:
        passages.append(_build_passage(current_chunk))

    return passages


def _build_passage(lines: list[TranscriptLine]) -> dict:
    """Build a passage dict from a group of lines."""
    first = lines[0]

    # Build text with speaker labels
    text_parts = []
    for line in lines:
        if line.speaker:
            text_parts.append(f"{line.speaker}: {line.text}")
        else:
            text_parts.append(line.text)
    text = "\n".join(text_parts)

    # Location label
    parts = []
    if first.season:
        parts.append(f"S{first.season.zfill(2)}")
    if first.episode:
        parts.append(f"E{first.episode.zfill(2)}")
    if first.episode_title:
        parts.append(f"- {first.episode_title}")
    location_label = "".join(parts) if parts else "Unknown"

    return {
        "text": text,
        "location_label": location_label,
        "start_pos": lines[0].line_order,
        "end_pos": lines[-1].line_order,
    }
