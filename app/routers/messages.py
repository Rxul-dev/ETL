from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.pagination import get_pagination_params, paginate_with_schema

router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])

@router.post("", response_model=schemas.MessageOut, status_code=201)
def send_message(chat_id: int, payload: schemas.MessageCreate, db: Session = Depends(get_db)):
    if not db.get(models.Chat, chat_id):
        raise HTTPException(404, detail="chat not found")
    m = models.Message(
        chat_id=chat_id,
        sender_id=payload.sender_id,
        body=payload.body,
        reply_to_id=payload.reply_to_id,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("", response_model=schemas.Page)  # o PageMessages si prefieres
def list_messages(chat_id: int, p=Depends(get_pagination_params), db: Session = Depends(get_db)):
    page, page_size = p
    q = (
        db.query(models.Message)
        .filter(models.Message.chat_id == chat_id)
        .order_by(models.Message.created_at.desc())
    )
    return paginate_with_schema(q, page, page_size, schemas.MessageOut)