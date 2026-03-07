from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.search.exact_match import search_exact
from app.search.semantic import search_semantic
from app.search.context import get_context_window
from app.search.mwe.idioms import search_idiom
from app.search.mwe.phrasal_verbs import search_phrasal_verb
from app.search.mwe.collocations import search_collocation
from app.models import Passage

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    mode: str = Field(default="exact", pattern="^(exact|semantic|idiom|phrasal_verb|collocation)$")
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
    elif request.mode == "idiom":
        data = search_idiom(
            db=db,
            query=request.query,
            source_id=request.source_id,
            limit=request.limit,
            offset=request.offset,
        )
    elif request.mode == "phrasal_verb":
        data = search_phrasal_verb(
            db=db,
            query=request.query,
            source_id=request.source_id,
            limit=request.limit,
            offset=request.offset,
        )
    elif request.mode == "collocation":
        # For collocation mode, search for the word pair in the corpus
        words = request.query.strip().split()
        if len(words) >= 2:
            data = search_collocation(
                db=db,
                word1=words[0],
                word2=" ".join(words[1:]),
                source_id=request.source_id,
                limit=request.limit,
                offset=request.offset,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Collocation search requires at least two words",
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
