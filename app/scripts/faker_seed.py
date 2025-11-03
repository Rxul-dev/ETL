import os, re
import random
from datetime import datetime, timedelta, timezone
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app import models


# ----------- Parámetros largos ----------

# USERS_COUNT = int(os.getenv("FAKER_USERS", "500"))
# GROUP_CHATS_COUNT = int(os.getenv("FAKER_GROUPS", "50"))
# DM_CHATS_COUNT = int(os.getenv("FAKER_DMS", "200"))

# MSGS_MIN = int(os.getenv("FAKER_MSGS_MIN", "200"))
# MSGS_MAX = int(os.getenv("FAKER_MSGS_MAX", "1000"))
# DAYS_WINDOW = int(os.getenv("FAKER_DAYS", "30"))

# BATCH_SIZE = int(os.getenv("FAKER_BATCH_SIZE", "1000"))



# ----------- Parámetros  cortos ----------
USERS_COUNT = int(os.getenv("FAKER_USERS", "60"))
GROUP_CHATS_COUNT = int(os.getenv("FAKER_GROUPS", "8"))
DM_CHATS_COUNT = int(os.getenv("FAKER_DMS", "12"))

MSGS_MIN = int(os.getenv("FAKER_MSGS_MIN", "5"))
MSGS_MAX = int(os.getenv("FAKER_MSGS_MAX", "15"))
DAYS_WINDOW = int(os.getenv("FAKER_DAYS", "14"))

BATCH_SIZE = int(os.getenv("FAKER_BATCH_SIZE", "500"))

# Reacciones
REACTIONS_PROB = float(os.getenv("FAKER_REACT_PROB", "0.35"))
REACTIONS_MAX_PER_MSG = int(os.getenv("FAKER_REACT_MAX", "3"))
REACTIONS_BATCH_SIZE = int(os.getenv("FAKER_REACT_BATCH", "2000"))
REACTIONS_SET = os.getenv("FAKER_REACT_SET", "👍,❤️,😂,🔥,😮,🙏").split(",")
BOOKING_MSG_PROB = float(os.getenv("BOOKING_MSG_PROB", "0.25"))

BOOKING_KEY_TEMPLATES = [
    "Quiero reservar una sala mañana a las 10",
    "Reserva una sala para {n} personas el {fecha} a las {hora}",
    "Podemos agendar un tour para {fecha}?",
    "Reservar mesa para {n} el {fecha} a las {hora}",
    "Necesito una sala el {fecha} por la mañana",
    "Booking request: room {fecha} {hora}",
]

# ----------- Utils ---------------
fake = Faker()
random.seed()

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def rand_dt_within(days: int) -> datetime:
    """Fecha aleatoria dentro de los últimos `days` días (aware/UTC)."""
    now = now_utc()
    days = max(1, days)
    delta = timedelta(
        days=random.randint(0, days - 1),
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

def pick_reactors(members: list[int], sender_id: int, k: int) -> list[int]:
    """Elige hasta k reactores distintos (evitando al remitente)."""
    pool = [m for m in members if m != sender_id]
    k = min(k, len(pool))
    return random.sample(pool, k) if k > 0 else []

def random_booking_text(now: datetime) -> str:
    d = now + timedelta(days=random.randint(1, 14))
    fecha = d.strftime("%Y-%m-%d")
    hora = f"{random.randint(8,20):02d}:00"
    n = random.choice([2, 3, 4, 5, 6])
    tpl = random.choice(BOOKING_KEY_TEMPLATES)
    return tpl.format(n=n, fecha=fecha, hora=hora)

def parse_booking_message_text(body: str) -> dict:
    """Heurística simple: detecta tipo (room/table/tour) y fecha tentativa."""
    body_l = (body or "").lower()

    if any(k in body_l for k in ["sala", "room"]):
        btype = "room"
    elif any(k in body_l for k in ["mesa", "table"]):
        btype = "table"
    elif "tour" in body_l:
        btype = "tour"
    else:
        btype = "generic"

    when = None
    if "mañana" in body_l or "tomorrow" in body_l:
        when = now_utc() + timedelta(days=1)

    # fecha YYYY-MM-DD
    m = re.search(r"(\d{4}-\d{2}-\d{2})", body_l)
    if m:
        try:
            f = m.group(1)
            when = datetime.strptime(f, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            pass

    # hora HH:MM
    h = re.search(r"(\d{1,2}:\d{2})", body_l)
    if h:
        try:
            hh, mm = h.group(1).split(":")
            base = when or now_utc()
            when = base.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        except Exception:
            pass

    return {"booking_type": btype, "booking_date": when}

# ---------------- Main ----------------
def main():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1) Usuarios existentes
        print("Leyendo usuarios existentes...")
        existing_handles = {h for (h,) in db.execute(select(models.User.handle)).all()}

        # 2) Crear usuarios
        print(f"Creando usuarios (target: {USERS_COUNT})...")
        new_users = []
        for _ in range(USERS_COUNT):
            handle = unique_handle(existing_handles)
            display_name = fake.name()[:120]
            u = models.User(
                handle=handle,
                display_name=display_name,
                created_at=rand_dt_within(DAYS_WINDOW)
            )
            new_users.append(u)
            if len(new_users) >= BATCH_SIZE:
                db.add_all(new_users)
                db.commit()
                new_users.clear()
        if new_users:
            db.add_all(new_users)
            db.commit()
            new_users.clear()

        # 2b) Leer todos los usuarios
        print("Cargando todos los usuarios para armar chats...")
        users = db.execute(select(models.User.id)).scalars().all()
        if len(users) < 2:
            raise RuntimeError("Se requieren al menos 2 usuarios para crear DMs y grupos.")

        # 3) Chats grupales
        print(f"Creando {GROUP_CHATS_COUNT} chats grupales...")
        created_groups: list[int] = []
        for _ in range(GROUP_CHATS_COUNT):
            c = models.Chat(
                type=models.ChatType.group,
                title=fake.catch_phrase()[:200],
                created_at=rand_dt_within(DAYS_WINDOW)
            )
            db.add(c)
            db.flush()
            members = pick_n(users, random.randint(5, min(20, len(users))))
            for uid in members:
                db.add(models.ChatMember(
                    chat_id=c.id,
                    user_id=uid,
                    joined_at=rand_dt_within(DAYS_WINDOW)
                ))
            created_groups.append(c.id)
        db.commit()

        # 4) Chats DM
        print(f"Creando {DM_CHATS_COUNT} chats DM...")
        created_dms: list[int] = []
        for _ in range(DM_CHATS_COUNT):
            a, b = random.sample(users, 2)
            c = models.Chat(
                type=models.ChatType.dm,
                title=None,
                created_at=rand_dt_within(DAYS_WINDOW)
            )
            db.add(c)
            db.flush()
            db.add(models.ChatMember(chat_id=c.id, user_id=a, joined_at=rand_dt_within(DAYS_WINDOW)))
            db.add(models.ChatMember(chat_id=c.id, user_id=b, joined_at=rand_dt_within(DAYS_WINDOW)))
            created_dms.append(c.id)
        db.commit()

        all_chats = created_groups + created_dms
        print(f"Total chats creados: {len(all_chats)}")

        # 5) Mensajes + Bookings
        print("Generando mensajes por chat...")
        total_msgs = 0
        total_bookings = 0
        total_events = 0

        for chat_id in all_chats:
            member_ids = db.execute(
                select(models.ChatMember.user_id).where(models.ChatMember.chat_id == chat_id)
            ).scalars().all()
            if not member_ids:
                member_ids = random.sample(users, k=2)

            n_msgs = random.randint(MSGS_MIN, MSGS_MAX)
            for _ in range(n_msgs):
                sender_id = random.choice(member_ids)
                body = fake.paragraph(nb_sentences=random.randint(1, 3))
                created_at = rand_dt_within(DAYS_WINDOW)

                # 8% de mensajes tipo booking
                if random.random() < 0.08:
                    body = random_booking_text(now_utc())

                m = models.Message(
                    chat_id=chat_id,
                    sender_id=sender_id,
                    body=body,
                    created_at=created_at
                )
                db.add(m)
                db.flush()

                # Detectar texto de reserva
                details = parse_booking_message_text(m.body)
                if details["booking_type"] != "generic":
                    b = models.Booking(
                        message_id=m.id,
                        user_id=m.sender_id,
                        chat_id=m.chat_id,
                        booking_type=details["booking_type"],
                        booking_date=details["booking_date"],
                        status="PENDING",
                        created_at=now_utc()
                    )
                    db.add(b)
                    db.flush()
                    db.add(models.BookingEvent(
                        booking_id=b.id,
                        event_type="created",
                        created_at=now_utc()
                    ))
                    # Confirmación del bot
                    if random.random() < 0.5:
                        db.add(models.Message(
                            chat_id=m.chat_id,
                            sender_id=1,
                            body=f" Booking #{b.id} creado exitosamente",
                            created_at=now_utc(),
                        ))
                    total_bookings += 1
                    total_events += 1

                # Commit por mensaje para mantener conteo preciso
                db.commit()
                total_msgs += 1

        # 6) Reacciones
        print("Generando reacciones...")
        reacts_buffer = []
        total_reacts = 0

        for chat_id in all_chats:
            member_ids = db.execute(
                select(models.ChatMember.user_id).where(models.ChatMember.chat_id == chat_id)
            ).scalars().all()
            if not member_ids:
                member_ids = random.sample(users, k=min(3, len(users)))

            last_id = 0
            while True:
                rows = db.execute(
                    select(models.Message.id, models.Message.sender_id)
                    .where(models.Message.chat_id == chat_id, models.Message.id > last_id)
                    .order_by(models.Message.id.asc())
                    .limit(5000)
                ).all()
                if not rows:
                    break

                for msg_id, sender_id in rows:
                    if random.random() > REACTIONS_PROB:
                        continue

                    k = random.randint(1, REACTIONS_MAX_PER_MSG)
                    reactors = pick_reactors(member_ids, sender_id, k)
                    used_users = set()
                    for uid in reactors:
                        if uid in used_users:
                            continue
                        emoji = random.choice(REACTIONS_SET)
                        reacts_buffer.append(models.Reaction(
                            message_id=msg_id,
                            user_id=uid,
                            emoji=emoji,
                            created_at=rand_dt_within(DAYS_WINDOW),
                        ))
                        used_users.add(uid)

                        if len(reacts_buffer) >= REACTIONS_BATCH_SIZE:
                            db.add_all(reacts_buffer)
                            db.commit()
                            total_reacts += len(reacts_buffer)
                            reacts_buffer.clear()
                last_id = rows[-1][0]

        if reacts_buffer:
            db.add_all(reacts_buffer)
            db.commit()
            total_reacts += len(reacts_buffer)
            reacts_buffer.clear()

        print(f" Listo! Usuarios: {len(users)} | Chats: {len(all_chats)} | Mensajes: {total_msgs} | Reacciones: {total_reacts} | Bookings: {total_bookings} | BookingEvents: {total_events}")
    finally:
        db.close()
        print(" Conexión a la base de datos cerrada correctamente.")

if __name__ == "__main__":
    main()