"""Backfill ChromaDB embeddings for passages already in PostgreSQL."""

import logging

from sqlalchemy import func

from app.database import SessionLocal
from app.models import Passage, Source
from app.nlp.embeddings import add_passages_to_chroma, chroma_passage_count, get_collection

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

        # Get all passage IDs already in ChromaDB so we can skip them
        collection = get_collection()
        chroma_ids = set()
        if existing > 0:
            result = collection.get(include=[], limit=existing)
            chroma_ids = set(result["ids"])
            logger.info(f"Loaded {len(chroma_ids)} existing IDs from ChromaDB")

        offset = 0
        processed = 0
        skipped = 0

        while offset < total:
            try:
                rows = (
                    db.query(Passage, Source)
                    .join(Source, Source.id == Passage.source_id)
                    .order_by(Passage.id)
                    .offset(offset)
                    .limit(batch_size)
                    .all()
                )
            except Exception:
                logger.warning("DB connection lost, reconnecting...")
                db.close()
                db = SessionLocal()
                continue

            if not rows:
                break

            # Filter out passages already in ChromaDB
            new_rows = [(p, s) for p, s in rows if str(p.id) not in chroma_ids]

            if new_rows:
                ids = [str(p.id) for p, s in new_rows]
                texts = [p.text for p, s in new_rows]
                metadatas = [
                    {
                        "source_id": str(s.id),
                        "source_title": s.title,
                        "location_label": p.location_label or "",
                    }
                    for p, s in new_rows
                ]
                add_passages_to_chroma(ids, texts, metadatas)
                processed += len(new_rows)

            skipped += len(rows) - len(new_rows)
            offset += batch_size

            if processed % 1000 < batch_size:
                logger.info(f"  {processed} embedded, {skipped} skipped, {offset}/{total} scanned")

        logger.info(f"Backfill complete. ChromaDB now has {chroma_passage_count()} passages")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
