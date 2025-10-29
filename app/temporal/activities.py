from __future__ import annotations
import asyncio
import math
import os
from typing import Any, Dict, List, Tuple
import httpx
from temporalio import activity

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

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
    return items

@activity.defn(name="extract_chats_and_members")
async def extract_chats_and_members(page_size: int = 250) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    chats: List[Dict[str, Any]] = []
    members: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        # chats
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

        # members por chat
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
    return chats, members

@activity.defn(name="extract_messages_for_chat")
async def extract_messages_for_chat(chat_id: int, page_size: int = 250) -> List[Dict[str, Any]]:
    msgs: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=60) as client:
        page = 1
        while True:
            r = await client.get(f"{API_BASE_URL}/chats/{chat_id}/messages", params={"page": page, "page_size": page_size})
            r.raise_for_status()
            data = r.json()
            msgs.extend(data["items"])
            if page >= data["total_pages"]:
                break
            page += 1
            activity.heartbeat()
    return msgs

# -------- Transformaciones separadas --------
@activity.defn(name="transform_users")
async def transform_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    for u in users:
        u["handle"] = (u["handle"] or "").strip()
        u["display_name"] = (u.get("display_name") or "").strip()
    return users

@activity.defn(name="transform_chats_members")
async def transform_chats_members(chats: List[Dict[str, Any]], members: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    return chats, members

@activity.defn(name="transform_messages")
async def transform_messages(msgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for m in msgs:
        body = m.get("body") or ""
        m["message_length"] = len(body)
        
        if "created_at" in m and isinstance(m["created_at"], str):
        
            pass
    return msgs

# -------- Load: escribe en DW --------
from temporalio import activity
import psycopg2
import psycopg2.extras
from datetime import datetime
import dateutil.parser as dtp

WAREHOUSE_URL = os.getenv("WAREHOUSE_URL", "postgresql://postgres:postgres@dw:5432/warehouse")

def _pg():
    return psycopg2.connect(WAREHOUSE_URL)

@activity.defn(name="load_dimensions")
async def load_dimensions(users: List[Dict[str, Any]], chats: List[Dict[str, Any]], members: List[Dict[str, Any]]) -> None:
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
            psycopg2.extras.execute_batch(cur,
                "INSERT INTO dim_users(user_id, handle, display_name, created_at) VALUES (%s,%s,%s,%s) \
                 ON CONFLICT (user_id) DO UPDATE SET handle=EXCLUDED.handle, display_name=EXCLUDED.display_name, created_at=EXCLUDED.created_at",
                [(u["id"], u["handle"], u.get("display_name"), u["created_at"]) for u in users],
                page_size=1000)
            psycopg2.extras.execute_batch(cur,
                "INSERT INTO dim_chats(chat_id, type, title, created_at) VALUES (%s,%s,%s,%s) \
                 ON CONFLICT (chat_id) DO UPDATE SET type=EXCLUDED.type, title=EXCLUDED.title, created_at=EXCLUDED.created_at",
                [(c["id"], c["type"], c.get("title"), c["created_at"]) for c in chats],
                page_size=1000)
            psycopg2.extras.execute_batch(cur,
                "INSERT INTO bridge_chat_members(chat_id, user_id, role, joined_at) VALUES (%s,%s,%s,%s) \
                 ON CONFLICT (chat_id, user_id) DO UPDATE SET role=EXCLUDED.role, joined_at=EXCLUDED.joined_at",
                [(m["chat_id"], m["user_id"], m.get("role"), m["joined_at"]) for m in members],
                page_size=2000)
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
                # parse y derivados
                created_at = dtp.parse(m["created_at"])
                created_day = created_at.date()
                created_hour = created_at.hour
                return (
                    m["id"], m["chat_id"], m.get("sender_id"), m.get("body"),
                    m.get("message_length", len(m.get("body") or "")),
                    created_at, created_day, created_hour, m.get("edited_at"), m.get("reply_to_id")
                )
            psycopg2.extras.execute_batch(cur,
                "INSERT INTO fact_messages(message_id, chat_id, sender_id, body, message_length, created_at, created_day, created_hour, edited_at, reply_to_id) \
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) \
                 ON CONFLICT (message_id) DO UPDATE SET \
                 body=EXCLUDED.body, message_length=EXCLUDED.message_length, created_at=EXCLUDED.created_at, created_day=EXCLUDED.created_day, created_hour=EXCLUDED.created_hour, edited_at=EXCLUDED.edited_at, reply_to_id=EXCLUDED.reply_to_id",
                [row(m) for m in msgs],
                page_size=5000)
        conn.commit()
        return len(msgs)
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