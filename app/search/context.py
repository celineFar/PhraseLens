"""Context window support: fetch surrounding passages for a matched passage."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Passage


def get_context_window(
    db: Session,
    passage_id: UUID,
    source_id: UUID,
    start_pos: int,
    window: int = 1,
) -> dict:
    """Fetch neighboring passages before and after the matched passage.

    Args:
        db: Database session
        passage_id: The matched passage ID
        source_id: Source to look within
        start_pos: The start_pos of the matched passage
        window: Number of passages to fetch on each side

    Returns:
        dict with 'before' and 'after' lists of passage texts
    """
    before = (
        db.query(Passage)
        .filter(
            Passage.source_id == source_id,
            Passage.start_pos < start_pos,
        )
        .order_by(Passage.start_pos.desc())
        .limit(window)
        .all()
    )
    before = [
        {"text": p.text, "location_label": p.location_label}
        for p in reversed(before)
    ]

    after = (
        db.query(Passage)
        .filter(
            Passage.source_id == source_id,
            Passage.start_pos > start_pos,
        )
        .order_by(Passage.start_pos.asc())
        .limit(window)
        .all()
    )
    after = [
        {"text": p.text, "location_label": p.location_label}
        for p in after
    ]

    return {"before": before, "after": after}
