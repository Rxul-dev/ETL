from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import users, chats, messages, reactions, etl_router, bookings as bookings_router, booking_events, websocket
from prometheus_fastapi_instrumentator import Instrumentator
import logging
import os

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rxul Chat API", version="1.0.0")

# Configurar CORS
# Obtener orígenes permitidos de variable de entorno o usar valores por defecto
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://91.98.64.119"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Métodos específicos
    allow_headers=["Content-Type", "Authorization", "Accept"],  # Headers específicos
)

# Instrumentar la API para Prometheus
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

app.include_router(users.router)
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(reactions.router)
app.include_router(etl_router.router)
app.include_router(bookings_router.router)
app.include_router(booking_events.router)
app.include_router(websocket.router)

@app.get("/")
def root():
    return {"ok": True, "service": "Rxul-chat"}