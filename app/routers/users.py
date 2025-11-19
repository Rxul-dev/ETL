from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.utils.pagination import get_pagination_params, paginate
from app.utils.pagination import get_pagination_params, paginate_with_schema

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=schemas.UserOut, status_code=201)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(handle=payload.handle).first():
        raise HTTPException(409, detail="handle already exists")
    u = models.User(handle=payload.handle, display_name=payload.display_name)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.get("/by-handle/{handle}", response_model=schemas.UserOut)
def get_user_by_handle(handle: str, db: Session = Depends(get_db)):
    """Obtiene un usuario por su handle. Debe ir antes de /{user_id} para que FastAPI lo evalúe correctamente."""
    u = db.query(models.User).filter_by(handle=handle).first()
    if not u:
        raise HTTPException(404, detail="user not found")
    return u


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(models.User, user_id)
    if not u:
        raise HTTPException(404, detail="user not found")
    return u


@router.get("", response_model=schemas.PageUsers)
def list_users(p=Depends(get_pagination_params), db: Session = Depends(get_db)):
    page, page_size = p
    q = db.query(models.User).order_by(models.User.created_at.desc())
    return paginate_with_schema(q, page, page_size, schemas.UserOut)