from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source, Passage

router = APIRouter(prefix="/api", tags=["sources"])


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.title).all()
    results = []
    for source in sources:
        passage_count = (
            db.query(func.count(Passage.id))
            .filter(Passage.source_id == source.id)
            .scalar()
        )
        results.append({
            "id": str(source.id),
            "title": source.title,
            "type": source.type,
            "author": source.author,
            "year": source.year,
            "passage_count": passage_count,
            "created_at": source.created_at.isoformat() if source.created_at else None,
        })
    return {"sources": results}


@router.get("/sources/{source_id}")
def get_source(source_id: UUID, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    passage_count = (
        db.query(func.count(Passage.id))
        .filter(Passage.source_id == source.id)
        .scalar()
    )
    return {
        "id": str(source.id),
        "title": source.title,
        "type": source.type,
        "author": source.author,
        "year": source.year,
        "metadata": source.metadata_,
        "passage_count": passage_count,
        "created_at": source.created_at.isoformat() if source.created_at else None,
    }
