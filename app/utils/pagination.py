import math
from fastapi import Query, HTTPException
from sqlalchemy.orm import Query as SAQuery
from typing import Tuple

MAX_PAGE_SIZE = 250

def get_pagination_params(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE)) -> Tuple[int,int]:
    if page_size > MAX_PAGE_SIZE:
        raise HTTPException(status_code=400, detail=f"page_size must be ≤ {MAX_PAGE_SIZE}")
    return page, page_size

def paginate(sa_query: SAQuery, page: int, page_size: int):
    total = sa_query.order_by(None).count()  # evitar ORDER BY costoso en count
    items = sa_query.limit(page_size).offset((page - 1) * page_size).all()
    total_pages = math.ceil(total / page_size) if page_size else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

def paginate_with_schema(sa_query: SAQuery, page: int, page_size: int, schema):
    total = sa_query.order_by(None).count()
    rows = sa_query.limit(page_size).offset((page - 1) * page_size).all()
    items = [schema.model_validate(r).model_dump() for r in rows]  # ORM -> dict
    total_pages = math.ceil(total / page_size) if page_size else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }