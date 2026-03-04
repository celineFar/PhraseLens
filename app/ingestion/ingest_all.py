"""Ingest all CSV files from the data directory on startup."""

import os
import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Source, Passage, LemmaIndex
from app.ingestion.csv_parser import parse_csv, identify_show
from app.ingestion.chunker import chunk_lines
from app.nlp.pipeline import tokenize_and_lemmatize

logger = logging.getLogger(__name__)


def ingest_all(db: Session) -> None:
    """Find all CSV files in the data directory and ingest any that haven't been ingested yet."""
    data_dir = settings.data_dir
    if not os.path.exists(data_dir):
        logger.warning(f"Data directory not found: {data_dir}")
        return

    csv_files = sorted(f for f in os.listdir(data_dir) if f.endswith(".csv"))
    if not csv_files:
        logger.info("No CSV files found in data directory")
        return

    logger.info(f"Found {len(csv_files)} CSV files in {data_dir}")

    for filename in csv_files:
        filepath = os.path.join(data_dir, filename)

        show_info = identify_show(filename)
        if show_info is None:
            logger.warning(f"Skipping unknown CSV format: {filename}")
            continue

        # Skip if already ingested
        existing = db.query(Source).filter(Source.title == show_info["title"]).first()
        if existing:
            logger.info(f"Already ingested: {show_info['title']} — skipping")
            continue

        logger.info(f"Ingesting: {show_info['title']} from {filename}")
        _ingest_file(db, filepath)


def _ingest_file(db: Session, filepath: str) -> None:
    show_title, transcript_lines = parse_csv(filepath)

    source = Source(title=show_title, type="tv_series")
    db.add(source)
    db.flush()

    passages = chunk_lines(transcript_lines, chunk_size=settings.chunk_size)
    logger.info(f"  {show_title}: {len(transcript_lines)} lines -> {len(passages)} passages")

    batch_size = 100
    for batch_start in range(0, len(passages), batch_size):
        batch = passages[batch_start : batch_start + batch_size]

        for p_dict in batch:
            nlp_result = tokenize_and_lemmatize(p_dict["text"])

            passage = Passage(
                source_id=source.id,
                text=p_dict["text"],
                start_pos=p_dict["start_pos"],
                end_pos=p_dict["end_pos"],
                location_label=p_dict["location_label"],
                tokens=nlp_result["tokens"],
                lemmas=nlp_result["lemmas"],
            )
            db.add(passage)
            db.flush()

            lemma_positions: dict[str, list[int]] = defaultdict(list)
            for pair in nlp_result["token_lemma_pairs"]:
                lemma = pair["lemma"]
                if len(lemma) > 1 or lemma.isalpha():
                    lemma_positions[lemma].append(pair["pos"])

            for lemma, positions in lemma_positions.items():
                db.add(LemmaIndex(
                    lemma=lemma,
                    passage_id=passage.id,
                    positions=positions,
                ))

        db.flush()
        done = min(batch_start + batch_size, len(passages))
        logger.info(f"  {show_title}: {done}/{len(passages)} passages processed")

    db.commit()
    logger.info(f"  {show_title}: done")
