from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.search.exact_match import search_exact

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    mode: str = Field(default="exact", pattern="^(exact)$")
    source_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


@router.post("/search")
def search(request: SearchRequest, db: Session = Depends(get_db)):
    if request.mode == "exact":
        return search_exact(
            db=db,
            query=request.query,
            source_id=request.source_id,
            limit=request.limit,
            offset=request.offset,
        )
