from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.search.exact_match import search_exact
from app.search.semantic import search_semantic
from app.search.context import get_context_window
from app.models import Passage

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    mode: str = Field(default="exact", pattern="^(exact|semantic)$")
    source_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    context_window: int = Field(default=0, ge=0, le=5)


@router.post("/search")
def search(request: SearchRequest, db: Session = Depends(get_db)):
    if request.mode == "exact":
        data = search_exact(
            db=db,
            query=request.query,
            source_id=request.source_id,
            limit=request.limit,
            offset=request.offset,
        )
    elif request.mode == "semantic":
        data = search_semantic(
            db=db,
            query=request.query,
            source_id=request.source_id,
            limit=request.limit,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {request.mode}")

    # Attach context window if requested
    if request.context_window > 0 and data.get("results"):
        for result in data["results"]:
            passage = db.query(Passage).filter(
                Passage.id == result["passage_id"]
            ).first()
            if passage:
                result["context"] = get_context_window(
                    db=db,
                    passage_id=passage.id,
                    source_id=passage.source_id,
                    start_pos=passage.start_pos or 0,
                    window=request.context_window,
                )

    return data
