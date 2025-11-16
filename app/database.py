from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Operacional (API)
DATABASE_URL = os.getenv( "DATABASE_URL","postgresql+psycopg2://postgres:postgres@localhost:5432/messaging")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Warehouse (ETL) - Opcional, solo se crea si está configurado
WAREHOUSE_URL = os.getenv("WAREHOUSE_URL")
warehouse_engine = None
WarehouseSession = None

if WAREHOUSE_URL:
    warehouse_engine = create_engine(
        WAREHOUSE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    WarehouseSession = sessionmaker(bind=warehouse_engine, autoflush=False, autocommit=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_dw():
    if not WarehouseSession:
        raise RuntimeError("WAREHOUSE_URL no está configurado. No se puede crear sesión de warehouse.")
    dw = WarehouseSession()
    try:
        yield dw
    finally:
        dw.close()