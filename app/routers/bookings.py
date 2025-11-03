from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import BookingCreate, BookingOut

router = APIRouter(prefix="/bookings", tags=["bookings"])

def _booking_to_dict(b: models.Booking) -> dict:
    return {
        "id": b.id,
        "chat_id": b.chat_id,
        "user_id": b.user_id,
        "message_id": b.message_id,
        "booking_type": b.booking_type,
        "booking_date": b.booking_date,
        "status": b.status,
        "created_at": b.created_at,
    }

@router.post("/", response_model=BookingOut)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    msg = db.query(models.Message).get(payload.message_id)
    if not msg:
        raise HTTPException(404, "Message not found")

    booking = models.Booking(
        message_id=payload.message_id,
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        booking_type=payload.booking_type,
        booking_date=payload.booking_date,
        status="PENDING",
    )
    db.add(booking)
    db.flush()
    evt = models.BookingEvent(booking_id=booking.id, event_type="created")
    db.add(evt)
    db.commit()
    db.refresh(booking)
    return booking

@router.get("", summary="List bookings (paginated)")
def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(250, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(models.Booking)
    total = q.count()
    items = (
        q.order_by(models.Booking.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size
    return {
        "items": [_booking_to_dict(b) for b in items],
        "total_pages": max(total_pages, 1),
    }

@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    b = db.query(models.Booking).get(booking_id)
    if not b:
        raise HTTPException(404, "Not found")
    return b