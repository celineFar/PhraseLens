import os
import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.ingestion.csv_parser import parse_csv
from app.ingestion.chunker import chunk_lines
from app.models import Source, Passage, LemmaIndex
from app.nlp.pipeline import tokenize_and_lemmatize
from app.nlp.embeddings import add_passages_to_chroma

router = APIRouter(prefix="/api", tags=["ingestion"])
logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
    filename: str = Field(..., description="CSV filename from the data directory")


@router.post("/ingest")
def ingest_csv(request: IngestRequest, db: Session = Depends(get_db)):
    filepath = os.path.join(settings.data_dir, request.filename)

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {request.filename}. Available files: {os.listdir(settings.data_dir)}",
        )

    # Check if already ingested
    show_title, transcript_lines = parse_csv(filepath)
    existing = db.query(Source).filter(Source.title == show_title).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Source '{show_title}' already ingested. Delete it first to re-ingest.",
        )

    logger.info(f"Ingesting '{show_title}' from {request.filename} ({len(transcript_lines)} lines)")

    # Create source
    source = Source(title=show_title, type="tv_series")
    db.add(source)
    db.flush()

    # Chunk lines into passages
    passage_dicts = chunk_lines(transcript_lines, chunk_size=settings.chunk_size)
    logger.info(f"Created {len(passage_dicts)} passages")

    # Process passages with NLP and build lemma index
    batch_size = 100
    total_passages = len(passage_dicts)

    for batch_start in range(0, total_passages, batch_size):
        batch = passage_dicts[batch_start : batch_start + batch_size]

        batch_passage_ids: list[str] = []
        batch_texts: list[str] = []
        batch_metadatas: list[dict] = []

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

            batch_passage_ids.append(str(passage.id))
            batch_texts.append(p_dict["text"])
            batch_metadatas.append({
                "source_id": str(source.id),
                "source_title": show_title,
                "location_label": p_dict["location_label"] or "",
            })

            # Build lemma index: group positions by lemma
            lemma_positions: dict[str, list[int]] = defaultdict(list)
            for pair in nlp_result["token_lemma_pairs"]:
                lemma = pair["lemma"]
                # Skip punctuation and very short tokens
                if len(lemma) > 1 or lemma.isalpha():
                    lemma_positions[lemma].append(pair["pos"])

            for lemma, positions in lemma_positions.items():
                db.add(LemmaIndex(
                    lemma=lemma,
                    passage_id=passage.id,
                    positions=positions,
                ))

        db.flush()

        if batch_texts:
            add_passages_to_chroma(batch_passage_ids, batch_texts, batch_metadatas)

        logger.info(f"Processed {min(batch_start + batch_size, total_passages)}/{total_passages} passages")

    db.commit()

    return {
        "status": "success",
        "source": {
            "id": str(source.id),
            "title": show_title,
        },
        "passages_created": total_passages,
    }


@router.get("/ingest/files")
def list_available_files():
    """List CSV files available for ingestion in the data directory."""
    data_dir = settings.data_dir
    if not os.path.exists(data_dir):
        return {"files": [], "data_dir": data_dir}

    files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    return {"files": sorted(files), "data_dir": data_dir}
