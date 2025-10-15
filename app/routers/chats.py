from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.pagination import get_pagination_params, paginate_with_schema

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("", response_model=schemas.ChatOut, status_code=201)
def create_chat(payload: schemas.ChatCreate, db: Session = Depends(get_db)):
    c = models.Chat(type=payload.type, title=payload.title)
    db.add(c)
    db.flush()
    for uid in payload.members:
        db.add(models.ChatMember(chat_id=c.id, user_id=uid))
    db.commit()
    db.refresh(c)
    return c

@router.get("", response_model=schemas.Page)
def list_chats(p=Depends(get_pagination_params), db: Session = Depends(get_db)):
    page, page_size = p
    q = db.query(models.Chat).order_by(models.Chat.created_at.desc())
    return paginate_with_schema(q, page, page_size, schemas.ChatOut)

@router.get("/{chat_id}", response_model=schemas.ChatOut)
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    c = db.get(models.Chat, chat_id)
    if not c:
        raise HTTPException(404, detail="chat not found")
    return c

@router.get("/{chat_id}/members", response_model=schemas.Page)
def list_members(chat_id: int, p=Depends(get_pagination_params), db: Session = Depends(get_db)):
    page, page_size = p
    q = (
        db.query(models.ChatMember)
        .filter(models.ChatMember.chat_id == chat_id)
        .order_by(models.ChatMember.joined_at.desc())
    )
    return paginate_with_schema(q, page, page_size, schemas.ChatMemberOut)