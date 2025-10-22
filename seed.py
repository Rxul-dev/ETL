from app.database import SessionLocal, Base, engine
from app import models

# Crea tablas si no existen
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Usuarios
u1 = models.User(handle="alice", display_name="Alice")
u2 = models.User(handle="bob", display_name="Bob")
db.add_all([u1, u2])
db.flush()  # para obtener ids

# Chat DM entre Alice y Bob
chat = models.Chat(type=models.ChatType.dm, title=None)
db.add(chat)
db.flush()

# Miembros del chat
db.add_all([
    models.ChatMember(chat_id=chat.id, user_id=u1.id),
    models.ChatMember(chat_id=chat.id, user_id=u2.id),
])

# Mensajes de ejemplo
db.add_all([
    models.Message(chat_id=chat.id, sender_id=u1.id, body="hola"),
    models.Message(chat_id=chat.id, sender_id=u2.id, body="pura vida"),
    models.Message(chat_id=chat.id, sender_id=u1.id, body="waza"),
])

db.commit()
db.close()
print("Seed listo ;D")