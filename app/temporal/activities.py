from __future__ import annotations
import os
from typing import Any, Dict, List, Tuple

import httpx
from temporalio import activity

import psycopg2
import psycopg2.extras
import dateutil.parser as dtp
from datetime import datetime, date
from decimal import Decimal

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
WAREHOUSE_URL = os.getenv("WAREHOUSE_URL", "postgresql://postgres:postgres@dw:5432/warehouse")


def _pg():
    return psycopg2.connect(WAREHOUSE_URL)

def _parse_ts(value: Any) -> datetime | None:
    if not value:
        return None
    dt = dtp.parse(value) if isinstance(value, str) else value
    if isinstance(dt, datetime):
        return dt
    return None

def _to_json_safe(val):
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, dict):
        return {k: _to_json_safe(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_to_json_safe(v) for v in val]
    return val


@activity.defn(name="extract_users")
async def extract_users(page_size: int = 250) -> List[Dict[str, Any]]:
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
    return _to_json_safe(items)


@activity.defn(name="extract_chats_and_members")
async def extract_chats_and_members(page_size: int = 250) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
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
    return _to_json_safe(chats), _to_json_safe(members)


@activity.defn(name="extract_messages_for_chat")
async def extract_messages_for_chat(chat_id: int, page_size: int = 250) -> List[Dict[str, Any]]:
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
    for u in users:
        u["handle"] = (u.get("handle") or "").strip()
        u["display_name"] = (u.get("display_name") or "").strip()
        if isinstance(u.get("created_at"), (datetime, date)):
            u["created_at"] = u["created_at"].isoformat()
    return _to_json_safe(users)


@activity.defn(name="transform_chats_members")
async def transform_chats_members(
    chats: List[Dict[str, Any]], members: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    for c in chats:
        if isinstance(c.get("created_at"), (datetime, date)):
            c["created_at"] = c["created_at"].isoformat()
    for m in members:
        if isinstance(m.get("joined_at"), (datetime, date)):
            m["joined_at"] = m["joined_at"].isoformat()
    return _to_json_safe(chats), _to_json_safe(members)


@activity.defn(name="transform_messages")
async def transform_messages(msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for m in msgs:
        body = m.get("body") or ""
        m["message_length"] = len(body)
        if isinstance(m.get("created_at"), (datetime, date)):
            m["created_at"] = m["created_at"].isoformat()
        if isinstance(m.get("edited_at"), (datetime, date)):
            m["edited_at"] = m["edited_at"].isoformat()
    return _to_json_safe(msgs)


@activity.defn(name="transform_reactions")
async def transform_reactions(recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for r in recs:
        if isinstance(r.get("created_at"), (datetime, date)):
            r["created_at"] = r["created_at"].isoformat()
        r["emoji"] = (r.get("emoji") or "").strip()
    return _to_json_safe(recs)


@activity.defn(name="load_dimensions")
async def load_dimensions(
    users: List[Dict[str, Any]], chats: List[Dict[str, Any]], members: List[Dict[str, Any]]
) -> None:
    conn = _pg(); conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dim_users(
              user_id INT PRIMARY KEY,
              handle TEXT,
              display_name TEXT,
              created_at TIMESTAMPTZ
            );
            CREATE TABLE IF NOT EXISTS dim_chats(
              chat_id INT PRIMARY KEY,
              type TEXT,
              title TEXT,
              created_at TIMESTAMPTZ
            );
            CREATE TABLE IF NOT EXISTS bridge_chat_members(
              chat_id INT,
              user_id INT,
              role TEXT,
              joined_at TIMESTAMPTZ,
              PRIMARY KEY(chat_id, user_id)
            );
            """)
        with conn.cursor() as cur:
            if users:
                psycopg2.extras.execute_batch(
                    cur,
                    """INSERT INTO dim_users(user_id, handle, display_name, created_at)
                       VALUES (%s,%s,%s,%s)
                       ON CONFLICT (user_id) DO UPDATE
                       SET handle=EXCLUDED.handle,
                           display_name=EXCLUDED.display_name,
                           created_at=EXCLUDED.created_at""",
                    [(u["id"], u.get("handle"), u.get("display_name"), u.get("created_at")) for u in users],
                    page_size=1000
                )
            if chats:
                psycopg2.extras.execute_batch(
                    cur,
                    """INSERT INTO dim_chats(chat_id, type, title, created_at)
                       VALUES (%s,%s,%s,%s)
                       ON CONFLICT (chat_id) DO UPDATE
                       SET type=EXCLUDED.type,
                           title=EXCLUDED.title,
                           created_at=EXCLUDED.created_at""",
                    [(c["id"], c.get("type"), c.get("title"), c.get("created_at")) for c in chats],
                    page_size=1000
                )
            if members:
                psycopg2.extras.execute_batch(
                    cur,
                    """INSERT INTO bridge_chat_members(chat_id, user_id, role, joined_at)
                       VALUES (%s,%s,%s,%s)
                       ON CONFLICT (chat_id, user_id) DO UPDATE
                       SET role=EXCLUDED.role,
                           joined_at=EXCLUDED.joined_at""",
                    [(m["chat_id"], m["user_id"], m.get("role"), m.get("joined_at")) for m in members],
                    page_size=2000
                )
        conn.commit()
    finally:
        conn.close()


@activity.defn(name="load_messages")
async def load_messages(msgs: List[Dict[str, Any]]) -> int:
    if not msgs:
        return 0
    conn = _pg(); conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_messages(
              message_id INT PRIMARY KEY,
              chat_id INT,
              sender_id INT,
              body TEXT,
              message_length INT,
              created_at TIMESTAMPTZ,
              created_day DATE,
              created_hour INT,
              edited_at TIMESTAMPTZ,
              reply_to_id INT
            );
            """)
            def row(m):
                created_at = _parse_ts(m.get("created_at"))
                created_day = created_at.date() if created_at else None
                created_hour = created_at.hour if created_at else None
                edited_at = _parse_ts(m.get("edited_at")) if m.get("edited_at") else None
                return (
                    m["id"], m["chat_id"], m.get("sender_id"), m.get("body"),
                    m.get("message_length", len(m.get("body") or "")),
                    created_at, created_day, created_hour, edited_at, m.get("reply_to_id")
                )
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
                [row(m) for m in msgs],
                page_size=5000
            )
        conn.commit()
        return len(msgs)
    finally:
        conn.close()


@activity.defn(name="load_reactions")
async def load_reactions(chat_id: int, reactions: List[Dict[str, Any]]) -> int:
    if not reactions:
        return 0
    conn = _pg(); conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS fact_reactions(
              message_id INT,
              chat_id INT,
              user_id INT,
              emoji TEXT,
              created_at TIMESTAMPTZ,
              created_day DATE,
              created_hour INT,
              PRIMARY KEY (message_id, user_id, emoji)
            );
            """)
            def row(r):
                ts = _parse_ts(r.get("created_at"))
                return (
                    r["message_id"],
                    chat_id,
                    r["user_id"],
                    r.get("emoji"),
                    ts,
                    ts.date() if ts else None,
                    ts.hour if ts else None
                )
            psycopg2.extras.execute_batch(
                cur,
                """INSERT INTO fact_reactions
                   (message_id, chat_id, user_id, emoji, created_at, created_day, created_hour)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (message_id, user_id, emoji) DO UPDATE SET
                     created_at=EXCLUDED.created_at,
                     created_day=EXCLUDED.created_day,
                     created_hour=EXCLUDED.created_hour""",
                [row(r) for r in reactions],
                page_size=5000
            )
        conn.commit()
        return len(reactions)
    finally:
        conn.close()


@activity.defn(name="get_chat_meta")
async def get_chat_meta(chat_id: int) -> Dict[str, Any]:
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


@activity.defn(name="etl_reactions_page")
async def etl_reactions_page(chat_id: int, page: int, page_size: int = 250) -> int:
    async with httpx.AsyncClient(timeout=60) as client:
        rm = await client.get(
            f"{API_BASE_URL}/chats/{chat_id}/messages",
            params={"page": page, "page_size": page_size},
        )
        rm.raise_for_status()
        mdata = rm.json()
        msgs = mdata.get("items", [])
    if not msgs:
        return 0
    all_reactions: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=60) as client:
        for m in msgs:
            mid = m["id"]
            rpage = 1
            while True:
                rr = await client.get(
                    f"{API_BASE_URL}/messages/{mid}/reactions",
                    params={"page": rpage, "page_size": 250}
                )
                rr.raise_for_status()
                rdata = rr.json()
                items = rdata.get("items", [])
                all_reactions.extend(items)
                if rpage >= rdata.get("total_pages", 1):
                    break
                rpage += 1
                activity.heartbeat()
    if not all_reactions:
        return 0
    all_reactions = await transform_reactions(all_reactions)
    inserted = await load_reactions(chat_id, all_reactions)
    return inserted