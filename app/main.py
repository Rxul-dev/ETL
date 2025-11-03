from fastapi import FastAPI
from app.database import Base, engine
from app.routers import users, chats, messages, reactions, etl_router, bookings as bookings_router, booking_events




Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rxul Chat API", version="1.0.0")

app.include_router(users.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(reactions.router)
app.include_router(etl_router.router)
app.include_router(bookings_router.router)
app.include_router(booking_events.router)

@app.get("/")
def root():
    return {"ok": True, "service": "Rxul-chat"}