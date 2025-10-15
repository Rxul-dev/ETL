from fastapi import FastAPI
from app.database import Base, engine
from app.routers import users, chats, messages, reactions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rxul Chat API", version="1.0.0")

app.include_router(users.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(reactions.router)

@app.get("/")
def root():
    return {"ok": True, "service": "Rxul-chat"}