"""Backfill ChromaDB embeddings for passages already in PostgreSQL."""

import logging
import sys

from sqlalchemy import func

from app.database import SessionLocal
from app.models import Passage, Source
from app.nlp.embeddings import add_passages_to_chroma, chroma_passage_count

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


def backfill(batch_size: int = 200) -> None:
    db = SessionLocal()
    try:
        total = db.query(func.count(Passage.id)).scalar()
        existing = chroma_passage_count()
        logger.info(f"PostgreSQL passages: {total}, ChromaDB passages: {existing}")

        if existing >= total:
            logger.info("ChromaDB is already up to date")
            return

        # Fetch all passages with source info, ordered for consistent batching
        offset = 0
        processed = 0

        while offset < total:
            rows = (
                db.query(Passage, Source)
                .join(Source, Source.id == Passage.source_id)
                .order_by(Passage.id)
                .offset(offset)
                .limit(batch_size)
                .all()
            )

            if not rows:
                break

            ids = [str(p.id) for p, s in rows]
            texts = [p.text for p, s in rows]
            metadatas = [
                {
                    "source_id": str(s.id),
                    "source_title": s.title,
                    "location_label": p.location_label or "",
                }
                for p, s in rows
            ]

            add_passages_to_chroma(ids, texts, metadatas)
            processed += len(rows)
            offset += batch_size
            logger.info(f"  {processed}/{total} passages embedded")

        logger.info(f"Backfill complete. ChromaDB now has {chroma_passage_count()} passages")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
