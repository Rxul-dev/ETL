from __future__ import annotations
import os
import logging
import asyncio
from typing import Any, Dict, List, Tuple, Optional

import httpx
from temporalio import activity

import psycopg2
import psycopg2.extras
import dateutil.parser as dtp
from datetime import datetime, date, timedelta
from decimal import Decimal

# Configurar logging estructurado
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
WAREHOUSE_URL = os.getenv("WAREHOUSE_URL", "postgresql://postgres:tes$a5410@dw:5432/warehouse")


def _pg():
    """Crea una conexión a PostgreSQL."""
    return psycopg2.connect(WAREHOUSE_URL)


def _parse_ts(value: Any) -> datetime | None:
    """Parsea un valor a datetime, retorna None si no es posible."""
    if not value:
        return None
    try:
        dt = dtp.parse(value) if isinstance(value, str) else value
        if isinstance(dt, datetime):
            return dt
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing timestamp {value}: {e}")
    return None


def _to_json_safe(val):
    """Convierte valores a tipos JSON-serializables."""
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, dict):
        return {k: _to_json_safe(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_to_json_safe(v) for v in val]
    return val


def _validate_user(u: Dict[str, Any]) -> bool:
    """Valida que un usuario tenga los campos requeridos."""
    if not u.get("id"):
        logger.warning(f"User sin ID: {u}")
        return False
    if not u.get("handle") and not u.get("display_name"):
        logger.warning(f"User {u.get('id')} sin handle ni display_name")
    return True


def _validate_chat(c: Dict[str, Any]) -> bool:
    """Valida que un chat tenga los campos requeridos."""
    if not c.get("id"):
        logger.warning(f"Chat sin ID: {c}")
        return False
    if not c.get("type"):
        logger.warning(f"Chat {c.get('id')} sin type")
    return True


def _validate_message(m: Dict[str, Any]) -> bool:
    """Valida que un mensaje tenga los campos requeridos."""
    if not m.get("id"):
        logger.warning(f"Message sin ID: {m}")
        return False
    if not m.get("chat_id"):
        logger.warning(f"Message {m.get('id')} sin chat_id")
        return False
    if not m.get("body"):
        logger.warning(f"Message {m.get('id')} sin body")
    if not m.get("created_at"):
        logger.warning(f"Message {m.get('id')} sin created_at")
        return False
    return True


def _validate_booking(b: Dict[str, Any]) -> bool:
    """Valida que un booking tenga los campos requeridos."""
    if not b.get("id"):
        logger.warning(f"Booking sin ID: {b}")
        return False
    if not b.get("status"):
        logger.warning(f"Booking {b.get('id')} sin status")
        return False
    if not b.get("created_at"):
        logger.warning(f"Booking {b.get('id')} sin created_at")
        return False
    return True


@activity.defn(name="extract_users")
async def extract_users(page_size: int = 250) -> List[Dict[str, Any]]:
    """Extrae usuarios desde la API con paginación."""
    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        page = 1
        while True:
            r = await client.get(f"{API_BASE_URL}/users", params={"page": page, "page_size": page_size})
            r.raise_for_status()
            data = r.json()
            items.extend(data["items"])
            if page >= data["total_pages"]:
                break
            page += 1
            activity.heartbeat()
    logger.info(f"Extracted {len(items)} users")
    return _to_json_safe(items)


@activity.defn(name="extract_chats_and_members")
async def extract_chats_and_members(page_size: int = 250) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extrae chats y sus miembros desde la API."""
    chats: List[Dict[str, Any]] = []
    members: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        page = 1
        while True:
            r = await client.get(f"{API_BASE_URL}/chats", params={"page": page, "page_size": page_size})
            r.raise_for_status()
            data = r.json()
            chats.extend(data["items"])
            if page >= data["total_pages"]:
                break
            page += 1
            activity.heartbeat()
        for c in chats:
            cid = c["id"]
            page = 1
            while True:
                r = await client.get(f"{API_BASE_URL}/chats/{cid}/members", params={"page": page, "page_size": page_size})
                r.raise_for_status()
                data = r.json()
                members.extend(data["items"])
                if page >= data["total_pages"]:
                    break
                page += 1
                activity.heartbeat()
    logger.info(f"Extracted {len(chats)} chats and {len(members)} members")
    return _to_json_safe(chats), _to_json_safe(members)


@activity.defn(name="extract_messages_for_chat")
async def extract_messages_for_chat(chat_id: int, page_size: int = 250) -> List[Dict[str, Any]]:
    """Extrae mensajes de un chat específico."""
    msgs: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=60) as client:
        page = 1
        while True:
            r = await client.get(f"{API_BASE_URL}/chats/{chat_id}/messages",
                                 params={"page": page, "page_size": page_size})
            r.raise_for_status()
            data = r.json()
            msgs.extend(data["items"])
            if page >= data["total_pages"]:
                break
            page += 1
            activity.heartbeat()
    return _to_json_safe(msgs)


@activity.defn(name="transform_users")
async def transform_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma y valida usuarios."""
    valid_users = []
    for u in users:
        if not _validate_user(u):
            continue
        u["handle"] = (u.get("handle") or "").strip()
        u["display_name"] = (u.get("display_name") or "").strip()
        if isinstance(u.get("created_at"), (datetime, date)):
            u["created_at"] = u["created_at"].isoformat()
        valid_users.append(u)
    logger.info(f"Transformed {len(valid_users)}/{len(users)} users")
    return _to_json_safe(valid_users)


@activity.defn(name="transform_chats_members")
async def transform_chats_members(
    chats: List[Dict[str, Any]], members: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Transforma y valida chats y miembros."""
    valid_chats = []
    for c in chats:
        if not _validate_chat(c):
            continue
        if isinstance(c.get("created_at"), (datetime, date)):
            c["created_at"] = c["created_at"].isoformat()
        valid_chats.append(c)
    
    valid_members = []
    for m in members:
        if not m.get("chat_id") or not m.get("user_id"):
            logger.warning(f"Member sin chat_id o user_id: {m}")
            continue
        if isinstance(m.get("joined_at"), (datetime, date)):
            m["joined_at"] = m["joined_at"].isoformat()
        valid_members.append(m)
    
    logger.info(f"Transformed {len(valid_chats)}/{len(chats)} chats and {len(valid_members)}/{len(members)} members")
    return _to_json_safe(valid_chats), _to_json_safe(valid_members)


@activity.defn(name="transform_messages")
async def transform_messages(msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma y valida mensajes."""
    valid_msgs = []
    for m in msgs:
        if not _validate_message(m):
            continue
        body = m.get("body") or ""
        m["message_length"] = len(body)
        if isinstance(m.get("created_at"), (datetime, date)):
            m["created_at"] = m["created_at"].isoformat()
        if isinstance(m.get("edited_at"), (datetime, date)):
            m["edited_at"] = m["edited_at"].isoformat()
        valid_msgs.append(m)
    logger.info(f"Transformed {len(valid_msgs)}/{len(msgs)} messages")
    return _to_json_safe(valid_msgs)


@activity.defn(name="transform_reactions")
async def transform_reactions(recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma y valida reacciones."""
    valid_recs = []
    for r in recs:
        if not r.get("message_id") or not r.get("user_id"):
            logger.warning(f"Reaction sin message_id o user_id: {r}")
            continue
        if isinstance(r.get("created_at"), (datetime, date)):
            r["created_at"] = r["created_at"].isoformat()
        r["emoji"] = (r.get("emoji") or "").strip()
        if not r["emoji"]:
            logger.warning(f"Reaction sin emoji: {r}")
            continue
        valid_recs.append(r)
    logger.info(f"Transformed {len(valid_recs)}/{len(recs)} reactions")
    return _to_json_safe(valid_recs)


@activity.defn(name="load_dimensions")
async def load_dimensions(
    users: List[Dict[str, Any]], chats: List[Dict[str, Any]], members: List[Dict[str, Any]]
) -> None:
    """Carga dimensiones (users, chats, members) en el warehouse."""
    conn = _pg()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # Crear tablas si no existen (con foreign keys)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dim_users(
              user_id INT PRIMARY KEY,
              handle TEXT NOT NULL,
              display_name TEXT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL
            );
            CREATE TABLE IF NOT EXISTS dim_chats(
              chat_id INT PRIMARY KEY,
              type TEXT NOT NULL,
              title TEXT,
              created_at TIMESTAMPTZ NOT NULL
            );
            CREATE TABLE IF NOT EXISTS bridge_chat_members(
              chat_id INT NOT NULL,
              user_id INT NOT NULL,
              role TEXT NOT NULL,
              joined_at TIMESTAMPTZ NOT NULL,
              PRIMARY KEY(chat_id, user_id),
              FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES dim_users(user_id) ON DELETE CASCADE
            );
            """)
        
        with conn.cursor() as cur:
            if users:
                rows = []
                for u in users:
                    created_at = _parse_ts(u.get("created_at"))
                    if not created_at:
                        logger.warning(f"User {u.get('id')} sin created_at válido, usando ahora")
                        created_at = datetime.utcnow()
                    rows.append((
                        u["id"],
                        u.get("handle") or "",
                        u.get("display_name") or "",
                        created_at
                    ))
                psycopg2.extras.execute_batch(
                    cur,
                    """INSERT INTO dim_users(user_id, handle, display_name, created_at)
                       VALUES (%s,%s,%s,%s)
                       ON CONFLICT (user_id) DO UPDATE
                       SET handle=EXCLUDED.handle,
                           display_name=EXCLUDED.display_name,
                           created_at=EXCLUDED.created_at""",
                    rows,
                    page_size=1000
                )
                logger.info(f"Loaded {len(rows)} users")
            
            if chats:
                rows = []
                for c in chats:
                    created_at = _parse_ts(c.get("created_at"))
                    if not created_at:
                        logger.warning(f"Chat {c.get('id')} sin created_at válido, usando ahora")
                        created_at = datetime.utcnow()
                    rows.append((
                        c["id"],
                        c.get("type") or "",
                        c.get("title"),
                        created_at
                    ))
                psycopg2.extras.execute_batch(
                    cur,
                    """INSERT INTO dim_chats(chat_id, type, title, created_at)
                       VALUES (%s,%s,%s,%s)
                       ON CONFLICT (chat_id) DO UPDATE
                       SET type=EXCLUDED.type,
                           title=EXCLUDED.title,
                           created_at=EXCLUDED.created_at""",
                    rows,
                    page_size=1000
                )
                logger.info(f"Loaded {len(rows)} chats")
            
            if members:
                rows = []
                for m in members:
                    joined_at = _parse_ts(m.get("joined_at"))
                    if not joined_at:
                        logger.warning(f"Member {m.get('chat_id')}/{m.get('user_id')} sin joined_at válido, usando ahora")
                        joined_at = datetime.utcnow()
                    rows.append((
                        m["chat_id"],
                        m["user_id"],
                        m.get("role") or "member",
                        joined_at
                    ))
                psycopg2.extras.execute_batch(
                    cur,
                    """INSERT INTO bridge_chat_members(chat_id, user_id, role, joined_at)
                       VALUES (%s,%s,%s,%s)
                       ON CONFLICT (chat_id, user_id) DO UPDATE
                       SET role=EXCLUDED.role,
                           joined_at=EXCLUDED.joined_at""",
                    rows,
                    page_size=2000
                )
                logger.info(f"Loaded {len(rows)} members")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading dimensions: {e}", exc_info=True)
        raise
    finally:
        conn.close()


@activity.defn(name="load_messages")
async def load_messages(msgs: List[Dict[str, Any]]) -> int:
    """Carga mensajes en el warehouse."""
    if not msgs:
        return 0
    conn = _pg()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_messages(
              message_id INT PRIMARY KEY,
              chat_id INT NOT NULL,
              sender_id INT,
              body TEXT NOT NULL,
              message_length INT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL,
              created_day DATE NOT NULL,
              created_hour SMALLINT NOT NULL,
              edited_at TIMESTAMPTZ,
              reply_to_id INT,
              FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
              FOREIGN KEY (sender_id) REFERENCES dim_users(user_id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_fact_messages_chat_date 
              ON fact_messages(chat_id, created_day);
            CREATE INDEX IF NOT EXISTS idx_fact_messages_sender_date 
              ON fact_messages(sender_id, created_day) WHERE sender_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_fact_messages_created_at 
              ON fact_messages(created_at);
            """)
            
            def row(m):
                created_at = _parse_ts(m.get("created_at"))
                if not created_at:
                    logger.warning(f"Message {m.get('id')} sin created_at válido, usando ahora")
                    created_at = datetime.utcnow()
                created_day = created_at.date()
                created_hour = created_at.hour
                edited_at = _parse_ts(m.get("edited_at")) if m.get("edited_at") else None
                body = m.get("body") or ""
                return (
                    m["id"],
                    m["chat_id"],
                    m.get("sender_id"),
                    body,
                    len(body),
                    created_at,
                    created_day,
                    created_hour,
                    edited_at,
                    m.get("reply_to_id")
                )
            
            rows = [row(m) for m in msgs]
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO fact_messages
                   (message_id, chat_id, sender_id, body, message_length, created_at,
                    created_day, created_hour, edited_at, reply_to_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (message_id) DO UPDATE SET
                     body=EXCLUDED.body,
                     message_length=EXCLUDED.message_length,
                     created_at=EXCLUDED.created_at,
                     created_day=EXCLUDED.created_day,
                     created_hour=EXCLUDED.created_hour,
                     edited_at=EXCLUDED.edited_at,
                     reply_to_id=EXCLUDED.reply_to_id""",
                rows,
                page_size=5000
            )
        conn.commit()
        logger.info(f"Loaded {len(rows)} messages")
        return len(rows)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading messages: {e}", exc_info=True)
        raise
    finally:
        conn.close()


@activity.defn(name="load_reactions")
async def load_reactions(chat_id: int, reactions: List[Dict[str, Any]]) -> int:
    """Carga reacciones en el warehouse."""
    if not reactions:
        return 0
    conn = _pg()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_reactions(
              message_id INT NOT NULL,
              chat_id INT NOT NULL,
              user_id INT NOT NULL,
              emoji TEXT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL,
              created_day DATE NOT NULL,
              created_hour SMALLINT NOT NULL,
              PRIMARY KEY (message_id, user_id, emoji),
              FOREIGN KEY (message_id) REFERENCES fact_messages(message_id) ON DELETE CASCADE,
              FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES dim_users(user_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_fact_reactions_chat_date 
              ON fact_reactions(chat_id, created_day);
            CREATE INDEX IF NOT EXISTS idx_fact_reactions_message 
              ON fact_reactions(message_id);
            """)
            
            def row(r):
                ts = _parse_ts(r.get("created_at"))
                if not ts:
                    logger.warning(f"Reaction sin created_at válido, usando ahora")
                    ts = datetime.utcnow()
                return (
                    r["message_id"],
                    chat_id,
                    r["user_id"],
                    r.get("emoji") or "",
                    ts,
                    ts.date(),
                    ts.hour
                )
            
            rows = [row(r) for r in reactions]
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO fact_reactions
                   (message_id, chat_id, user_id, emoji, created_at, created_day, created_hour)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (message_id, user_id, emoji) DO UPDATE SET
                     created_at=EXCLUDED.created_at,
                     created_day=EXCLUDED.created_day,
                     created_hour=EXCLUDED.created_hour""",
                rows,
                page_size=5000
            )
        conn.commit()
        logger.info(f"Loaded {len(rows)} reactions for chat {chat_id}")
        return len(rows)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading reactions: {e}", exc_info=True)
        raise
    finally:
        conn.close()


@activity.defn(name="get_chat_meta")
async def get_chat_meta(chat_id: int) -> Dict[str, Any]:
    """Obtiene metadata de un chat (total de páginas de mensajes)."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{API_BASE_URL}/chats/{chat_id}/messages",
            params={"page": 1, "page_size": 1},
        )
        r.raise_for_status()
        data = r.json()
        return {"total_pages": data.get("total_pages", 1)}


@activity.defn(name="etl_messages_page")
async def etl_messages_page(chat_id: int, page: int, page_size: int = 250) -> int:
    """ETL de una página de mensajes. (Mantenido para compatibilidad)"""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(
            f"{API_BASE_URL}/chats/{chat_id}/messages",
            params={"page": page, "page_size": page_size},
        )
        r.raise_for_status()
        data = r.json()
        msgs = data.get("items", [])
    if not msgs:
        return 0
    msgs = await transform_messages(msgs)
    inserted = await load_messages(msgs)
    return inserted


@activity.defn(name="etl_messages_chat")
async def etl_messages_chat(chat_id: int, page_size: int = 1000) -> Dict[str, Any]:
    """
    ETL de TODOS los mensajes de un chat completo.
    Reduce drásticamente el número de actividades en el workflow.
    Retorna: {"messages_loaded": int, "total_pages": int}
    """
    all_msgs: List[Dict[str, Any]] = []
    total_pages = 0
    
    async with httpx.AsyncClient(timeout=300) as client:  # Timeout más largo para chats grandes
        page = 1
        while True:
            try:
                r = await client.get(
                    f"{API_BASE_URL}/chats/{chat_id}/messages",
                    params={"page": page, "page_size": page_size},
                )
                r.raise_for_status()
                data = r.json()
                items = data.get("items", [])
                if not items:
                    break
                all_msgs.extend(items)
                total_pages = int(data.get("total_pages", 1))
                if page >= total_pages:
                    break
                page += 1
                activity.heartbeat()  # Heartbeat durante paginación larga
            except Exception as e:
                logger.error(f"Error fetching messages for chat {chat_id}, page {page}: {e}")
                break
    
    if not all_msgs:
        logger.info(f"No messages found for chat {chat_id}")
        return {"messages_loaded": 0, "total_pages": 0}
    
    # Transformar y cargar todos los mensajes
    msgs = await transform_messages(all_msgs)
    inserted = await load_messages(msgs)
    
    logger.info(f"Loaded {inserted} messages from chat {chat_id} ({total_pages} pages)")
    return {"messages_loaded": inserted, "total_pages": total_pages}


@activity.defn(name="etl_reactions_chat")
async def etl_reactions_chat(chat_id: int, page_size: int = 1000) -> Dict[str, Any]:
    """
    ETL de TODAS las reacciones de un chat completo.
    Procesa todos los mensajes del chat y obtiene sus reacciones en paralelo.
    Reduce drásticamente el número de actividades en el workflow.
    Retorna: {"reactions_loaded": int, "messages_processed": int}
    """
    logger.info(f"Starting etl_reactions_chat for chat {chat_id}")
    activity.heartbeat()
    
    # Primero obtener todos los mensajes del chat
    all_msgs: List[Dict[str, Any]] = []
    
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            page = 1
            while True:
                try:
                    logger.debug(f"Fetching messages page {page} for chat {chat_id}")
                    r = await client.get(
                        f"{API_BASE_URL}/chats/{chat_id}/messages",
                        params={"page": page, "page_size": page_size},
                    )
                    r.raise_for_status()
                    data = r.json()
                    items = data.get("items", [])
                    if not items:
                        break
                    all_msgs.extend(items)
                    total_pages = int(data.get("total_pages", 1))
                    logger.debug(f"Chat {chat_id}: page {page}/{total_pages}, total messages so far: {len(all_msgs)}")
                    if page >= total_pages:
                        break
                    page += 1
                    activity.heartbeat()  # Heartbeat después de cada página
                except Exception as e:
                    logger.error(f"Error fetching messages for reactions, chat {chat_id}, page {page}: {e}", exc_info=True)
                    break
    except Exception as e:
        logger.error(f"Fatal error fetching messages for chat {chat_id}: {e}", exc_info=True)
        raise
    
    if not all_msgs:
        logger.info(f"No messages found for chat {chat_id}, skipping reactions")
        return {"reactions_loaded": 0, "messages_processed": 0}
    
    logger.info(f"Found {len(all_msgs)} messages in chat {chat_id}, fetching reactions...")
    activity.heartbeat()
    
    # Obtener reacciones en paralelo para todos los mensajes
    all_reactions: List[Dict[str, Any]] = []
    
    async def fetch_reactions_for_message(mid: int) -> List[Dict[str, Any]]:
        """Obtiene todas las reacciones de un mensaje (paginado)."""
        reactions = []
        reaction_page_size = 250  # Máximo permitido por la API (MAX_PAGE_SIZE)
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:  # Timeout más corto por mensaje
                rpage = 1
                while True:
                    try:
                        rr = await client.get(
                            f"{API_BASE_URL}/messages/{mid}/reactions",
                            params={"page": rpage, "page_size": reaction_page_size}
                        )
                        # Manejar específicamente errores 422 (page_size demasiado grande)
                        if rr.status_code == 422:
                            # Intentar con page_size más pequeño
                            logger.debug(f"422 error for message {mid}, retrying with smaller page_size")
                            rr = await client.get(
                                f"{API_BASE_URL}/messages/{mid}/reactions",
                                params={"page": rpage, "page_size": 100}
                            )
                        
                        rr.raise_for_status()
                        rdata = rr.json()
                        items = rdata.get("items", [])
                        if not items:
                            break
                        reactions.extend(items)
                        if rpage >= rdata.get("total_pages", 1):
                            break
                        rpage += 1
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 422:
                            logger.warning(f"422 Unprocessable Entity for message {mid}, page {rpage}. Skipping this message.")
                        else:
                            logger.warning(f"HTTP error {e.response.status_code} fetching reactions for message {mid}, page {rpage}: {e}")
                        break
                    except Exception as e:
                        logger.warning(f"Error fetching reactions for message {mid}, page {rpage}: {e}")
                        break
        except Exception as e:
            logger.warning(f"Fatal error fetching reactions for message {mid}: {e}")
        return reactions
    
    # Procesar mensajes en lotes paralelos (máximo 20 a la vez para evitar saturación)
    batch_size = 20
    message_ids = [m["id"] for m in all_msgs]
    total_batches = (len(message_ids) + batch_size - 1) // batch_size
    
    logger.info(f"Processing {len(message_ids)} messages in {total_batches} batches of {batch_size}")
    
    for i in range(0, len(message_ids), batch_size):
        batch = message_ids[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        logger.debug(f"Processing batch {batch_num}/{total_batches} for chat {chat_id} ({len(batch)} messages)")
        
        try:
            tasks = [fetch_reactions_for_message(mid) for mid in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.warning(f"Error fetching reactions batch {batch_num}, message {batch[idx]}: {result}")
                elif isinstance(result, list):
                    all_reactions.extend(result)
            
            logger.debug(f"Batch {batch_num}/{total_batches} completed: {len(all_reactions)} total reactions so far")
        except Exception as e:
            logger.error(f"Error processing batch {batch_num} for chat {chat_id}: {e}", exc_info=True)
        
        # Heartbeat después de cada batch para mantener la actividad viva
        activity.heartbeat()
    
    logger.info(f"Finished fetching reactions for chat {chat_id}: {len(all_reactions)} reactions from {len(all_msgs)} messages")
    activity.heartbeat()
    
    if not all_reactions:
        logger.info(f"No reactions found for chat {chat_id}")
        return {"reactions_loaded": 0, "messages_processed": len(all_msgs)}
    
    # Transformar y cargar todas las reacciones
    logger.info(f"Transforming and loading {len(all_reactions)} reactions for chat {chat_id}")
    activity.heartbeat()
    
    try:
        all_reactions = await transform_reactions(all_reactions)
        inserted = await load_reactions(chat_id, all_reactions)
        
        logger.info(f"Successfully loaded {inserted} reactions from {len(all_msgs)} messages in chat {chat_id}")
        return {"reactions_loaded": inserted, "messages_processed": len(all_msgs)}
    except Exception as e:
        logger.error(f"Error transforming/loading reactions for chat {chat_id}: {e}", exc_info=True)
        raise


@activity.defn(name="etl_reactions_page")
async def etl_reactions_page(chat_id: int, page: int, page_size: int = 250) -> int:
    """
    ETL de reacciones para una página de mensajes.
    Optimizado: procesa múltiples mensajes en paralelo y usa batch más grande.
    """
    # Aumentar page_size para mensajes si es muy pequeño (optimización)
    effective_page_size = max(page_size, 500)  # Mínimo 500 mensajes por batch
    
    async with httpx.AsyncClient(timeout=60) as client:
        rm = await client.get(
            f"{API_BASE_URL}/chats/{chat_id}/messages",
            params={"page": page, "page_size": effective_page_size},
        )
        rm.raise_for_status()
        mdata = rm.json()
        msgs = mdata.get("items", [])
    
    if not msgs:
        return 0
    
    # Obtener reacciones en paralelo para todos los mensajes
    all_reactions: List[Dict[str, Any]] = []
    
    async def fetch_reactions_for_message(mid: int) -> List[Dict[str, Any]]:
        """Obtiene todas las reacciones de un mensaje (paginado)."""
        reactions = []
        reaction_page_size = 250  # Máximo permitido por la API (MAX_PAGE_SIZE)
        
        async with httpx.AsyncClient(timeout=60) as client:
            rpage = 1
            while True:
                try:
                    rr = await client.get(
                        f"{API_BASE_URL}/messages/{mid}/reactions",
                        params={"page": rpage, "page_size": reaction_page_size}
                    )
                    # Manejar específicamente errores 422 (page_size demasiado grande)
                    if rr.status_code == 422:
                        # Intentar con page_size más pequeño
                        logger.debug(f"422 error for message {mid}, retrying with smaller page_size")
                        rr = await client.get(
                            f"{API_BASE_URL}/messages/{mid}/reactions",
                            params={"page": rpage, "page_size": 100}
                        )
                    
                    rr.raise_for_status()
                    rdata = rr.json()
                    items = rdata.get("items", [])
                    if not items:
                        break
                    reactions.extend(items)
                    if rpage >= rdata.get("total_pages", 1):
                        break
                    rpage += 1
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 422:
                        logger.warning(f"422 Unprocessable Entity for message {mid}, page {rpage}. Skipping this message.")
                    else:
                        logger.warning(f"HTTP error {e.response.status_code} fetching reactions for message {mid}, page {rpage}: {e}")
                    break
                except Exception as e:
                    logger.warning(f"Error fetching reactions for message {mid}: {e}")
                    break
        return reactions
    
    # Procesar mensajes en lotes paralelos (máximo 20 a la vez para no saturar)
    batch_size = 20
    message_ids = [m["id"] for m in msgs]
    
    for i in range(0, len(message_ids), batch_size):
        batch = message_ids[i:i + batch_size]
        tasks = [fetch_reactions_for_message(mid) for mid in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, Exception):
                logger.warning(f"Error fetching reactions batch: {result}")
            elif isinstance(result, list):
                all_reactions.extend(result)
        
        activity.heartbeat()
    
    if not all_reactions:
        return 0
    
    all_reactions = await transform_reactions(all_reactions)
    inserted = await load_reactions(chat_id, all_reactions)
    logger.info(f"Processed {len(msgs)} messages, loaded {inserted} reactions for chat {chat_id}, page {page}")
    return inserted


# --- Booking activities ---
@activity.defn(name="parse_booking_message")
async def parse_booking_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heurística simple para detectar intención de reserva a partir del cuerpo del mensaje.
    Devuelve un diccionario JSON-serializable con tipo y fecha estimada.
    """
    body = (message.get("body") or "").lower()
    booking_type = "generic"
    if "sala" in body or "room" in body:
        booking_type = "room"
    elif "tour" in body:
        booking_type = "tour"
    elif "mesa" in body or "table" in body:
        booking_type = "table"

    when: datetime | None = None
    if "mañana" in body or "tomorrow" in body:
        when = datetime.utcnow() + timedelta(days=1)

    return _to_json_safe({
        "booking_type": booking_type,
        "booking_date": when,
    })


@activity.defn(name="create_booking_from_message")
async def create_booking_from_message(message: Dict[str, Any]) -> int:
    """
    Crea el booking vía tu API (no usa ORM local).
    Espera que exista un endpoint POST /bookings que devuelva {id: ...}.
    """
    details = await parse_booking_message(message)
    payload = {
        "message_id": message["id"],
        "user_id": message["sender_id"],
        "chat_id": message["chat_id"],
        "booking_type": details.get("booking_type"),
        "booking_date": details.get("booking_date"),
        "status": "PENDING",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE_URL}/bookings", json=_to_json_safe(payload))
        r.raise_for_status()
        data = r.json()

    return int(data["id"])


@activity.defn(name="send_booking_confirmation")
async def send_booking_confirmation(chat_id: int, booking_id: int) -> None:
    """
    Envía un mensaje automático al chat confirmando la creación del booking.
    Espera que exista POST /chats/{chat_id}/messages.
    """
    body = f" Booking #{booking_id} creado exitosamente."
    payload = {
        "chat_id": chat_id,
        "sender_id": 1,   
        "body": body,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{API_BASE_URL}/chats/{chat_id}/messages", json=_to_json_safe(payload))
        r.raise_for_status()

# ---------- Bookings (ETL) ----------
@activity.defn(name="extract_bookings")
async def extract_bookings(page_size: int = 250) -> List[Dict[str, Any]]:
    """
    Extrae bookings desde la API.
    NOTA: Para grandes volúmenes, usa etl_bookings que procesa directamente.
    """
    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        page = 1
        while True:
            r = await client.get(f"{API_BASE_URL}/bookings", params={"page": page, "page_size": page_size})
            r.raise_for_status()
            data = r.json()
            items.extend(data["items"])
            if page >= data["total_pages"]:
                break
            page += 1
            activity.heartbeat()
    logger.info(f"Extracted {len(items)} bookings")
    return _to_json_safe(items)


@activity.defn(name="etl_bookings")
async def etl_bookings(page_size: int = 1000) -> Dict[str, Any]:
    """
    ETL completo de bookings: extrae, transforma y carga directamente.
    Evita el problema de límite de tamaño de Temporal al no retornar todos los datos.
    Retorna solo un resumen: {"bookings_loaded": int}
    """
    logger.info("Starting etl_bookings")
    activity.heartbeat()
    
    # Extraer bookings página por página y procesar en lotes
    all_bookings: List[Dict[str, Any]] = []
    total_pages = 0
    processed_count = 0
    batch_size = 5000  # Procesar en lotes de 5000 para evitar problemas de memoria
    
    async with httpx.AsyncClient(timeout=300) as client:
        page = 1
        while True:
            try:
                logger.debug(f"Fetching bookings page {page}")
                r = await client.get(f"{API_BASE_URL}/bookings", params={"page": page, "page_size": page_size})
                r.raise_for_status()
                data = r.json()
                items = data.get("items", [])
                if not items:
                    break
                all_bookings.extend(items)
                total_pages = int(data.get("total_pages", 1))
                logger.debug(f"Bookings page {page}/{total_pages}, total so far: {len(all_bookings)}")
                
                # Procesar en lotes para evitar problemas de memoria y límite de tamaño
                if len(all_bookings) >= batch_size:
                    batch = all_bookings[:batch_size]
                    all_bookings = all_bookings[batch_size:]
                    
                    # Transformar y cargar el lote
                    batch = await transform_bookings(batch)
                    inserted = await load_bookings(batch)
                    processed_count += inserted
                    logger.info(f"Processed batch: {inserted} bookings loaded (total so far: {processed_count})")
                    activity.heartbeat()
                
                if page >= total_pages:
                    break
                page += 1
                activity.heartbeat()
            except Exception as e:
                logger.error(f"Error fetching bookings page {page}: {e}", exc_info=True)
                break
    
    # Procesar el último lote si queda algo
    if all_bookings:
        logger.info(f"Processing final batch of {len(all_bookings)} bookings")
        all_bookings = await transform_bookings(all_bookings)
        inserted = await load_bookings(all_bookings)
        processed_count += inserted
        activity.heartbeat()
    
    logger.info(f"Successfully loaded {processed_count} bookings from {total_pages} pages")
    return {"bookings_loaded": processed_count}


@activity.defn(name="transform_bookings")
async def transform_bookings(bookings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte fechas y normaliza campos de bookings."""
    valid_bookings = []
    for b in bookings:
        if not _validate_booking(b):
            continue
        if isinstance(b.get("created_at"), (datetime, date)):
            b["created_at"] = b["created_at"].isoformat()
        if isinstance(b.get("booking_date"), (datetime, date)):
            b["booking_date"] = b["booking_date"].isoformat()
        valid_bookings.append(b)
    logger.info(f"Transformed {len(valid_bookings)}/{len(bookings)} bookings")
    return _to_json_safe(valid_bookings)


@activity.defn(name="load_bookings")
async def load_bookings(bookings: List[Dict[str, Any]]) -> int:
    """Carga los bookings en la tabla fact_bookings del warehouse."""
    if not bookings:
        return 0
    conn = _pg()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_bookings(
              booking_id INT PRIMARY KEY,
              chat_id INT NOT NULL,
              user_id INT NOT NULL,
              message_id INT,
              booking_type TEXT,
              booking_date TIMESTAMPTZ,
              status TEXT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL,
              created_day DATE NOT NULL,
              created_hour SMALLINT NOT NULL,
              FOREIGN KEY (chat_id) REFERENCES dim_chats(chat_id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES dim_users(user_id) ON DELETE CASCADE,
              FOREIGN KEY (message_id) REFERENCES fact_messages(message_id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_fact_bookings_date_status 
              ON fact_bookings(created_day, status);
            CREATE INDEX IF NOT EXISTS idx_fact_bookings_chat 
              ON fact_bookings(chat_id);
            """)
            
            def row(b):
                created = _parse_ts(b.get("created_at"))
                if not created:
                    logger.warning(f"Booking {b.get('id')} sin created_at válido, usando ahora")
                    created = datetime.utcnow()
                return (
                    b["id"],
                    b.get("chat_id"),
                    b.get("user_id"),
                    b.get("message_id"),
                    b.get("booking_type"),
                    _parse_ts(b.get("booking_date")),
                    b.get("status") or "PENDING",
                    created,
                    created.date(),
                    created.hour
                )
            
            rows = [row(b) for b in bookings]
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO fact_bookings
                   (booking_id, chat_id, user_id, message_id, booking_type, booking_date,
                    status, created_at, created_day, created_hour)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (booking_id) DO UPDATE SET
                     booking_type=EXCLUDED.booking_type,
                     booking_date=EXCLUDED.booking_date,
                     status=EXCLUDED.status,
                     created_at=EXCLUDED.created_at,
                     created_day=EXCLUDED.created_day,
                     created_hour=EXCLUDED.created_hour""",
                rows,
                page_size=2000
            )
        conn.commit()
        logger.info(f"Loaded {len(rows)} bookings")
        return len(rows)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading bookings: {e}", exc_info=True)
        raise
    finally:
        conn.close()


# ---------- Booking Events (ETL) ----------
@activity.defn(name="extract_booking_events")
async def extract_booking_events(page_size: int = 250) -> List[Dict[str, Any]]:
    """
    Extrae eventos de reservas desde la API.
    NOTA: Para grandes volúmenes, usa etl_booking_events que procesa directamente.
    """
    items: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        page = 1
        while True:
            r = await client.get(f"{API_BASE_URL}/booking-events", params={"page": page, "page_size": page_size})
            r.raise_for_status()
            data = r.json()
            items.extend(data["items"])
            if page >= data["total_pages"]:
                break
            page += 1
            activity.heartbeat()
    logger.info(f"Extracted {len(items)} booking events")
    return _to_json_safe(items)


@activity.defn(name="etl_booking_events")
async def etl_booking_events(page_size: int = 1000) -> Dict[str, Any]:
    """
    ETL completo de booking events: extrae, transforma y carga directamente.
    Evita el problema de límite de tamaño de Temporal al no retornar todos los datos.
    Retorna solo un resumen: {"events_loaded": int}
    """
    logger.info("Starting etl_booking_events")
    activity.heartbeat()
    
    # Extraer eventos página por página y procesar en lotes
    all_events: List[Dict[str, Any]] = []
    total_pages = 0
    processed_count = 0
    batch_size = 5000  # Procesar en lotes de 5000 para evitar problemas de memoria
    
    async with httpx.AsyncClient(timeout=300) as client:
        page = 1
        while True:
            try:
                logger.debug(f"Fetching booking events page {page}")
                r = await client.get(f"{API_BASE_URL}/booking-events", params={"page": page, "page_size": page_size})
                r.raise_for_status()
                data = r.json()
                items = data.get("items", [])
                if not items:
                    break
                all_events.extend(items)
                total_pages = int(data.get("total_pages", 1))
                logger.debug(f"Booking events page {page}/{total_pages}, total so far: {len(all_events)}")
                
                # Procesar en lotes para evitar problemas de memoria y límite de tamaño
                if len(all_events) >= batch_size:
                    batch = all_events[:batch_size]
                    all_events = all_events[batch_size:]
                    
                    # Transformar y cargar el lote
                    batch = await transform_booking_events(batch)
                    inserted = await load_booking_events(batch)
                    processed_count += inserted
                    logger.info(f"Processed batch: {inserted} events loaded (total so far: {processed_count})")
                    activity.heartbeat()
                
                if page >= total_pages:
                    break
                page += 1
                activity.heartbeat()
            except Exception as e:
                logger.error(f"Error fetching booking events page {page}: {e}", exc_info=True)
                break
    
    # Procesar el último lote si queda algo
    if all_events:
        logger.info(f"Processing final batch of {len(all_events)} booking events")
        all_events = await transform_booking_events(all_events)
        inserted = await load_booking_events(all_events)
        processed_count += inserted
        activity.heartbeat()
    
    logger.info(f"Successfully loaded {processed_count} booking events from {total_pages} pages")
    return {"events_loaded": processed_count}


@activity.defn(name="transform_booking_events")
async def transform_booking_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte fechas de los eventos."""
    valid_events = []
    for e in events:
        if not e.get("id"):
            logger.warning(f"Booking event sin ID: {e}")
            continue
        if not e.get("booking_id"):
            logger.warning(f"Booking event {e.get('id')} sin booking_id")
            continue
        if not e.get("event_type"):
            logger.warning(f"Booking event {e.get('id')} sin event_type")
            continue
        if isinstance(e.get("created_at"), (datetime, date)):
            e["created_at"] = e["created_at"].isoformat()
        valid_events.append(e)
    logger.info(f"Transformed {len(valid_events)}/{len(events)} booking events")
    return _to_json_safe(valid_events)


@activity.defn(name="load_booking_events")
async def load_booking_events(events: List[Dict[str, Any]]) -> int:
    """Carga los eventos en la tabla fact_booking_events."""
    if not events:
        return 0
    conn = _pg()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # CORREGIDO: Usar INT PRIMARY KEY en lugar de SERIAL para usar el ID de la API
            cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_booking_events(
              event_id INT PRIMARY KEY,
              booking_id INT NOT NULL,
              event_type TEXT NOT NULL,
              created_at TIMESTAMPTZ NOT NULL,
              created_day DATE NOT NULL,
              created_hour SMALLINT NOT NULL,
              FOREIGN KEY (booking_id) REFERENCES fact_bookings(booking_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_fact_booking_events_booking 
              ON fact_booking_events(booking_id);
            CREATE INDEX IF NOT EXISTS idx_fact_booking_events_date 
              ON fact_booking_events(created_day);
            """)
            
            def row(e):
                created = _parse_ts(e.get("created_at"))
                if not created:
                    logger.warning(f"Booking event {e.get('id')} sin created_at válido, usando ahora")
                    created = datetime.utcnow()
                return (
                    e.get("id"),  # Usar ID de la API
                    e.get("booking_id"),
                    e.get("event_type") or "",
                    created,
                    created.date(),
                    created.hour
                )
            
            rows = [row(e) for e in events]
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO fact_booking_events
                   (event_id, booking_id, event_type, created_at, created_day, created_hour)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (event_id) DO UPDATE SET
                     booking_id=EXCLUDED.booking_id,
                     event_type=EXCLUDED.event_type,
                     created_at=EXCLUDED.created_at,
                     created_day=EXCLUDED.created_day,
                     created_hour=EXCLUDED.created_hour""",
                rows,
                page_size=3000
            )
        conn.commit()
        logger.info(f"Loaded {len(rows)} booking events")
        return len(rows)
    except Exception as e:
        conn.rollback()
        logger.error(f"Error loading booking events: {e}", exc_info=True)
        raise
    finally:
        conn.close()

# ========== INCREMENTAL ETL ==========
@activity.defn(name="extract_incremental_dimensions")
async def extract_incremental_dimensions(since: str | None, page_size: int = 250):
    """
    Devuelve (users, chats, members) modificados desde 'since'.
    - since puede ser ISO (p.ej. '2025-11-08T16:00:00Z') o el token 'watermark:auto'
    - Si la API no soporta filtros por fecha, cae en extracción completa y lo dejas igual.
    """
    # Resolver watermark específico por entidad
    if (since or "").lower() == "watermark:auto":
        wm_users = await _get_watermark("users")
        wm_chats = await _get_watermark("chats")
        wm_members = await _get_watermark("members")
        since_users = wm_users or datetime(1970, 1, 1)
        since_chats = wm_chats or datetime(1970, 1, 1)
        since_members = wm_members or datetime(1970, 1, 1)
    elif since:
        since_dt = _parse_ts(since) or datetime(1970, 1, 1)
        since_users = since_chats = since_members = since_dt
    else:
        since_users = since_chats = since_members = datetime(1970, 1, 1)

    users: List[Dict[str, Any]] = []
    chats: List[Dict[str, Any]] = []
    members: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30) as client:
        # ---- USERS ----
        page = 1
        while True:
            try:
                r = await client.get(f"{API_BASE_URL}/users", params={"page_size": page_size, "page": page, "since": since_users.isoformat()})
                r.raise_for_status()
            except Exception:
                # Fallback: extracción completa
                users = await extract_users(page_size)
                break
            data = r.json()
            users.extend(data.get("items", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
            activity.heartbeat()

        # ---- CHATS ----
        page = 1
        while True:
            try:
                r = await client.get(f"{API_BASE_URL}/chats", params={"page_size": page_size, "page": page, "since": since_chats.isoformat()})
                r.raise_for_status()
            except Exception:
                # Fallback: extracción completa
                full_chats, full_members = await extract_chats_and_members(page_size)
                chats = full_chats
                members = full_members
                break
            data = r.json()
            chats.extend(data.get("items", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
            activity.heartbeat()

        # ---- MEMBERS ----
        if not members:  # si no vino por fallback anterior
            for c in chats:
                cid = c["id"]
                page = 1
                while True:
                    try:
                        r = await client.get(
                            f"{API_BASE_URL}/chats/{cid}/members",
                            params={"page_size": page_size, "page": page, "since": since_members.isoformat()},
                        )
                        r.raise_for_status()
                    except Exception:
                        # Fallback: sin filtro
                        r = await client.get(
                            f"{API_BASE_URL}/chats/{cid}/members",
                            params={"page": page, "page_size": page_size},
                        )
                        r.raise_for_status()
                    data = r.json()
                    members.extend(data.get("items", []))
                    if page >= data.get("total_pages", 1):
                        break
                    page += 1
                    activity.heartbeat()

    logger.info(f"Extracted incremental: {len(users)} users, {len(chats)} chats, {len(members)} members")
    return _to_json_safe(users), _to_json_safe(chats), _to_json_safe(members)


@activity.defn(name="plan_incremental_message_pages")
async def plan_incremental_message_pages(since: str | None, page_size: int = 250) -> List[Dict[str, Any]]:
    """
    Devuelve una lista de páginas a procesar en formato:
      [{"chat_id": <id>, "page": <n>}, ...]
    Calculado consultando cuántas páginas de mensajes existen 'desde' esa fecha.
    Si la API no soporta 'since', asume total_pages sobre todo el histórico (conservador).
    """
    if (since or "").lower() == "watermark:auto":
        wm = await _get_watermark("messages")
        since_dt = wm or datetime(1970, 1, 1)
    elif since:
        since_dt = _parse_ts(since) or datetime(1970, 1, 1)
    else:
        since_dt = datetime(1970, 1, 1)

    # Trae chats (sin necesidad de members)
    chats, _members = await extract_chats_and_members(page_size)
    pages: List[Dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for c in chats:
            cid = c["id"]
            # Intentamos pedir meta con filtro 'since'
            params = {"page": 1, "page_size": 1, "since": since_dt.isoformat()}
            try:
                r = await client.get(f"{API_BASE_URL}/chats/{cid}/messages", params=params)
                r.raise_for_status()
                total_pages = int(r.json().get("total_pages", 1))
            except Exception:
                # Fallback: sin filtro
                r = await client.get(f"{API_BASE_URL}/chats/{cid}/messages", params={"page": 1, "page_size": 1})
                r.raise_for_status()
                total_pages = int(r.json().get("total_pages", 1))

            for p in range(1, total_pages + 1):
                pages.append({"chat_id": cid, "page": p})
            activity.heartbeat()

    logger.info(f"Planned {len(pages)} message pages for incremental ETL")
    return _to_json_safe(pages)


@activity.defn(name="update_watermark")
async def update_watermark(entity: str, ts_iso: str) -> None:
    """
    Persiste un watermark específico por entidad para reusarlo en corridas incrementales.
    Entidades: 'users', 'chats', 'members', 'messages', 'bookings', 'booking_events'
    """
    ts = _parse_ts(ts_iso) or datetime.utcnow()
    conn = _pg()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS etl_watermarks(
                    key TEXT PRIMARY KEY,
                    value TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            cur.execute("""
                INSERT INTO etl_watermarks(key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET 
                    value = EXCLUDED.value,
                    updated_at = NOW();
            """, (entity, ts))
        conn.commit()
        logger.info(f"Updated watermark for {entity} to {ts.isoformat()}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating watermark for {entity}: {e}", exc_info=True)
        raise
    finally:
        conn.close()


# ---------- Helpers internos para watermark ----------
async def _get_watermark(key: str) -> datetime | None:
    """Obtiene el watermark para una entidad específica."""
    conn = _pg()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS etl_watermarks(key TEXT PRIMARY KEY, value TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW());")
            cur.execute("SELECT value FROM etl_watermarks WHERE key = %s;", (key,))
            row = cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()