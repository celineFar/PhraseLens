"""Collocations API endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.search.mwe.collocations import get_collocations

router = APIRouter(prefix="/api", tags=["collocations"])


@router.get("/collocations/{word}")
def collocations(
    word: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get top collocates for a target word, ranked by PMI score."""
    return get_collocations(db=db, word=word, limit=limit)
