from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum

# ------------------- Tipos base -------------------

class ChatType(str, Enum):
    dm = "dm"
    group = "group"

# ------------------- USERS -------------------

class UserCreate(BaseModel):
    handle: str
    display_name: str

class UserOut(BaseModel):
    id: int
    handle: str
    display_name: str
    created_at: datetime

    class Config:
        from_attributes = True

# ------------------- CHATS -------------------

class ChatCreate(BaseModel):
    type: ChatType
    title: Optional[str] = None
    members: List[int] = Field(default_factory=list, description="IDs de usuarios que se añadirán al chat")

class ChatOut(BaseModel):
    id: int
    type: ChatType
    title: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMemberOut(BaseModel):
    chat_id: int
    user_id: int
    role: Optional[str] = "member"
    joined_at: datetime

    class Config:
        from_attributes = True

# ------------------- MESSAGES -------------------

class MessageCreate(BaseModel):
    body: str
    sender_id: int
    reply_to_id: Optional[int] = None

class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_id: Optional[int]
    body: str
    created_at: datetime
    edited_at: Optional[datetime] = None
    reply_to_id: Optional[int] = None

    class Config:
        from_attributes = True

# ------------------- REACTIONS -------------------

class ReactionCreate(BaseModel):
    emoji: str
    user_id: int

class ReactionOut(BaseModel):
    message_id: int
    user_id: int
    emoji: str
    created_at: datetime

    class Config:
        from_attributes = True

# ------------------- PAGINACIÓN -------------------

class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

class Page(BaseModel):
    """Modelo genérico para paginación (sin tipado de items)."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

class PageUsers(BaseModel):
    items: List[UserOut]
    total: int
    page: int
    page_size: int
    total_pages: int

class PageChats(BaseModel):
    items: List[ChatOut]
    total: int
    page: int
    page_size: int
    total_pages: int

class PageChatMembers(BaseModel):
    items: List[ChatMemberOut]
    total: int
    page: int
    page_size: int
    total_pages: int

class PageMessages(BaseModel):
    items: List[MessageOut]
    total: int
    page: int
    page_size: int
    total_pages: int

class PageReactions(BaseModel):
    items: List[ReactionOut]
    total: int
    page: int
    page_size: int
    total_pages: int

# BOOKING
class BookingCreate(BaseModel):
    message_id: int
    user_id: int
    chat_id: int
    booking_type: Optional[str] = "room"
    booking_date: Optional[datetime] = None

class BookingEventOut(BaseModel):
    id: int
    event_type: str
    created_at: datetime
    class Config: from_attributes = True

class BookingOut(BaseModel):
    id: int
    message_id: int
    user_id: int
    chat_id: int
    booking_type: Optional[str]
    booking_date: Optional[datetime]
    status: str
    created_at: datetime
    events: List[BookingEventOut] = []
    class Config: from_attributes = True