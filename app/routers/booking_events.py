from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/booking-events", tags=["bookings"])

def _event_to_dict(e: models.BookingEvent) -> dict:
    return {
        "id": e.id,
        "booking_id": e.booking_id,
        "event_type": e.event_type,
        "created_at": e.created_at,
    }

@router.get("", summary="List booking events (paginated)")
def list_booking_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(250, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(models.BookingEvent)
    total = q.count()
    items = (
        q.order_by(models.BookingEvent.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size
    return {
        "items": [_event_to_dict(e) for e in items],
        "total_pages": max(total_pages, 1),
    }