from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.pagination import get_pagination_params, paginate
from app.utils.pagination import get_pagination_params, paginate_with_schema

router = APIRouter(prefix="/messages/{message_id}/reactions", tags=["reactions"])

@router.post("", response_model=schemas.ReactionOut, status_code=201)
def add_reaction(message_id: int, payload: schemas.ReactionCreate, db: Session = Depends(get_db)):
    if not db.get(models.Message, message_id):
        raise HTTPException(404, detail="message not found")
    r = models.Reaction(message_id=message_id, user_id=payload.user_id, emoji=payload.emoji)
    db.add(r)
    db.commit()
    return r

@router.get("", response_model=schemas.Page)
def list_reactions(message_id: int, p=Depends(get_pagination_params), db: Session = Depends(get_db)):
    page, page_size = p
    q = (
        db.query(models.Reaction)
        .filter(models.Reaction.message_id == message_id)
        .order_by(models.Reaction.created_at.desc())
    )
    return paginate(q, page, page_size)

@router.delete("")
def remove_reaction(message_id: int, user_id: int, emoji: str, db: Session = Depends(get_db)):
    count = (
        db.query(models.Reaction)
        .filter_by(message_id=message_id, user_id=user_id, emoji=emoji)
        .delete()
    )
    db.commit()
    if count == 0:
        raise HTTPException(404, detail="reaction not found")
    return {"removed": True}


@router.get("", response_model=schemas.PageReactions)
def list_reactions(message_id: int, p=Depends(get_pagination_params), db: Session = Depends(get_db)):
    page, page_size = p
    q = (db.query(models.Reaction)
           .filter(models.Reaction.message_id == message_id)
           .order_by(models.Reaction.created_at.desc()))
    return paginate_with_schema(q, page, page_size, schemas.ReactionOut)