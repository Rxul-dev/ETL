import os
import math
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app import models

"""
Seeder masivo con Faker para la API de mensajería (usuarios, chats, miembros y mensajes).

Parámetros (variables de entorno opcionales):
- FAKER_USERS:           cantidad de usuarios a crear (default: 500)
- FAKER_GROUPS:          cantidad de chats grupales (default: 50)
- FAKER_DMS:             cantidad de chats DM (default: 200)
- FAKER_MSGS_MIN:        mínimo de mensajes por chat (default: 200)
- FAKER_MSGS_MAX:        máximo de mensajes por chat (default: 1000)
- FAKER_DAYS:            ventana de días hacia atrás para fechas (default: 30)
- FAKER_BATCH_SIZE:      tamaño de lote para commits (default: 1000)

Ejemplo:
docker compose exec api python scripts/faker_seed.py
"""

# ----------- Parámetros ----------
USERS_COUNT = int(os.getenv("FAKER_USERS", "500"))
GROUP_CHATS_COUNT = int(os.getenv("FAKER_GROUPS", "50"))
DM_CHATS_COUNT = int(os.getenv("FAKER_DMS", "200"))

MSGS_MIN = int(os.getenv("FAKER_MSGS_MIN", "200"))
MSGS_MAX = int(os.getenv("FAKER_MSGS_MAX", "1000"))
DAYS_WINDOW = int(os.getenv("FAKER_DAYS", "30"))

BATCH_SIZE = int(os.getenv("FAKER_BATCH_SIZE", "1000"))

# ----------- Utils ---------------
fake = Faker()
random.seed()

def rand_dt_within(days: int) -> datetime:
    """Fecha aleatoria dentro de los últimos `days` días."""
    now = datetime.utcnow()
    delta = timedelta(
        days=random.randint(0, max(days, 1) - 1),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return now - delta

def unique_handle(existing: set[str]) -> str:
    while True:
        base = fake.user_name()[:30].lower().replace(".", "_").replace("-", "_")
        handle = f"{base}_{random.randint(1000, 9999)}"
        if handle not in existing:
            existing.add(handle)
            return handle

def pick_n(seq, n):
    n = min(n, len(seq))
    return random.sample(seq, n) if n > 0 else []

# ----------- Main ----------------
def main():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # 1) Cargar handles existentes para evitar UNIQUE violation
    print("Leyendo usuarios existentes...")
    existing_handles = set()
    for (h,) in db.execute(select(models.User.handle)).all():
        existing_handles.add(h)

    # 2) Crear usuarios
    print(f"Creando usuarios (target: {USERS_COUNT})...")
    new_users = []
    for _ in range(USERS_COUNT):
        handle = unique_handle(existing_handles)
        display_name = fake.name()[:120]
        u = models.User(handle=handle, display_name=display_name, created_at=rand_dt_within(DAYS_WINDOW))
        new_users.append(u)
        if len(new_users) >= BATCH_SIZE:
            db.add_all(new_users)
            db.commit()
            new_users.clear()
    if new_users:
        db.add_all(new_users)
        db.commit()
        new_users.clear()

    # Obtener TODOS los usuarios (incluyendo los que ya existían)
    print("Cargando todos los usuarios para armar chats...")
    users = db.execute(select(models.User.id)).scalars().all()
    if len(users) < 2:
        raise RuntimeError("Se requieren al menos 2 usuarios para crear DMs y grupos.")

    # 3) Crear chats grupales
    print(f"Creando {GROUP_CHATS_COUNT} chats grupales...")
    created_groups = []
    for _ in range(GROUP_CHATS_COUNT):
        c = models.Chat(type=models.ChatType.group, title=fake.catch_phrase()[:200], created_at=rand_dt_within(DAYS_WINDOW))
        db.add(c)
        db.flush()
        # miembros: 5–20 aleatorios
        members = pick_n(users, random.randint(5, min(20, len(users))))
        for uid in members:
            db.add(models.ChatMember(chat_id=c.id, user_id=uid, joined_at=rand_dt_within(DAYS_WINDOW)))
        created_groups.append(c.id)
        if len(created_groups) % BATCH_SIZE == 0:
            db.commit()
    db.commit()

    # 4) Crear chats DM
    print(f"Creando {DM_CHATS_COUNT} chats DM...")
    created_dms = []
    for _ in range(DM_CHATS_COUNT):
        # escoger dos usuarios distintos
        a, b = random.sample(users, 2)
        c = models.Chat(type=models.ChatType.dm, title=None, created_at=rand_dt_within(DAYS_WINDOW))
        db.add(c)
        db.flush()
        db.add(models.ChatMember(chat_id=c.id, user_id=a, joined_at=rand_dt_within(DAYS_WINDOW)))
        db.add(models.ChatMember(chat_id=c.id, user_id=b, joined_at=rand_dt_within(DAYS_WINDOW)))
        created_dms.append(c.id)
        if len(created_dms) % BATCH_SIZE == 0:
            db.commit()
    db.commit()

    all_chats = created_groups + created_dms
    print(f"Total chats creados: {len(all_chats)}")

    # 5) Crear mensajes en cada chat
    print("Generando mensajes por chat...")
    msgs_buffer = []
    total_msgs = 0

    for chat_id in all_chats:
        # elegir un conjunto de posibles remitentes (miembros del chat)
        member_ids = db.execute(
            select(models.ChatMember.user_id).where(models.ChatMember.chat_id == chat_id)
        ).scalars().all()

        if not member_ids:
            # fallback: si no hay miembros por algún motivo, escogemos 2 al azar
            member_ids = random.sample(users, k=2)

        n_msgs = random.randint(MSGS_MIN, MSGS_MAX)
        for _ in range(n_msgs):
            sender_id = random.choice(member_ids)
            body = fake.paragraph(nb_sentences=random.randint(1, 3))
            created_at = rand_dt_within(DAYS_WINDOW)
            m = models.Message(
                chat_id=chat_id,
                sender_id=sender_id,
                body=body,
                created_at=created_at
            )
            msgs_buffer.append(m)

            if len(msgs_buffer) >= BATCH_SIZE:
                db.add_all(msgs_buffer)
                db.commit()
                total_msgs += len(msgs_buffer)
                msgs_buffer.clear()

    if msgs_buffer:
        db.add_all(msgs_buffer)
        db.commit()
        total_msgs += len(msgs_buffer)
        msgs_buffer.clear()

    print(f"Listo Usuarios totales: {len(users)} | Chats nuevos: {len(all_chats)} | Mensajes creados: {total_msgs}")
    db.close()

if __name__ == "__main__":
    main()