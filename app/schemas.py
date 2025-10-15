from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ChatType(str, Enum):
    dm = 'dm'
    group = 'group'

# ---- Users ----
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

# ---- Chats ----
class ChatCreate(BaseModel):
    type: ChatType
    title: Optional[str] = None
    members: List[int] = Field(default_factory=list, description="user_ids to add")

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
    role: str
    joined_at: datetime
    class Config:
        from_attributes = True

# ---- Messages ----
class MessageCreate(BaseModel):
    body: str
    reply_to_id: Optional[int] = None
    sender_id: int

class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_id: Optional[int]
    body: str
    created_at: datetime
    edited_at: Optional[datetime]
    reply_to_id: Optional[int]
    class Config:
        from_attributes = True

# ---- Reactions ----
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

# ---- Pagination ----
class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int

class Page(BaseModel):
    items: list
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


class PageUsers(BaseModel):
    items: List[UserOut]; total: int; page: int; page_size: int; total_pages: int

class PageChats(BaseModel):
    items: List[ChatOut]; total: int; page: int; page_size: int; total_pages: int

class PageChatMembers(BaseModel):
    items: List[ChatMemberOut]; total: int; page: int; page_size: int; total_pages: int

class PageMessages(BaseModel):
    items: List[MessageOut]; total: int; page: int; page_size: int; total_pages: int

class PageReactions(BaseModel):
    items: List[ReactionOut]; total: int; page: int; page_size: int; total_pages: int