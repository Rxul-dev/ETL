import os
import math
import time
import argparse
import requests
import psycopg2
import psycopg2.extras
from urllib.parse import urljoin
from datetime import datetime

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WAREHOUSE_URL = os.getenv("WAREHOUSE_URL", "postgresql://postgres:postgres@localhost:5432/warehouse")
DDL_PATH = os.path.join(os.path.dirname(__file__), "ddl.sql")

PAGE_SIZE = 250

def get_json(url, params=None):
    params = params or {}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_paginated(resource_url):
    page = 1
    total = None
    while True:
        data = get_json(resource_url, params={"page": page, "page_size": PAGE_SIZE})
        if total is None:
            total = data.get("total", 0)
        items = data.get("items", [])
        if not items:
            break
        yield from items
        if page * PAGE_SIZE >= total:
            break
        page += 1

def ensure_db(conn):
    with conn, conn.cursor() as cur:
        with open(DDL_PATH, "r", encoding="utf-8") as ddl:
            cur.execute(ddl.read())

def upsert_users(conn, rows):
    sql = """
    INSERT INTO dim_users (user_id, handle, display_name, created_at)
    VALUES (%(id)s, %(handle)s, %(display_name)s, %(created_at)s)
    ON CONFLICT (user_id) DO UPDATE SET
      handle = EXCLUDED.handle,
      display_name = EXCLUDED.display_name,
      created_at = EXCLUDED.created_at;
    """
    with conn, conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=1000)

def upsert_chats(conn, rows):
    sql = """
    INSERT INTO dim_chats (chat_id, type, title, created_at)
    VALUES (%(id)s, %(type)s, %(title)s, %(created_at)s)
    ON CONFLICT (chat_id) DO UPDATE SET
      type = EXCLUDED.type,
      title = EXCLUDED.title,
      created_at = EXCLUDED.created_at;
    """
    with conn, conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=1000)

def upsert_chat_members(conn, rows):
    sql = """
    INSERT INTO bridge_chat_members (chat_id, user_id, role, joined_at)
    VALUES (%(chat_id)s, %(user_id)s, %(role)s, %(joined_at)s)
    ON CONFLICT (chat_id, user_id) DO UPDATE SET
      role = EXCLUDED.role,
      joined_at = EXCLUDED.joined_at;
    """
    with conn, conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=1000)

def upsert_messages(conn, rows):
    sql = """
    INSERT INTO fact_messages (message_id, chat_id, sender_id, body, message_length, created_at, edited_at, reply_to_id, created_day, created_hour)
    VALUES (%(id)s, %(chat_id)s, %(sender_id)s, %(body)s, %(message_length)s, %(created_at)s, %(edited_at)s, %(reply_to_id)s, %(created_day)s, %(created_hour)s)
    ON CONFLICT (message_id) DO UPDATE SET
      chat_id = EXCLUDED.chat_id,
      sender_id = EXCLUDED.sender_id,
      body = EXCLUDED.body,
      message_length = EXCLUDED.message_length,
      created_at = EXCLUDED.created_at,
      edited_at = EXCLUDED.edited_at,
      reply_to_id = EXCLUDED.reply_to_id,
      created_day = EXCLUDED.created_day,
      created_hour = EXCLUDED.created_hour;
    """
    with conn, conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, rows, page_size=1000)

def transform_message(m):
    created_at = datetime.fromisoformat(m["created_at"].replace("Z","")) if isinstance(m["created_at"], str) else m["created_at"]
    created_day = created_at.date()
    created_hour = created_at.hour
    return {
        "id": m["id"],
        "chat_id": m["chat_id"],
        "sender_id": m.get("sender_id"),
        "body": m["body"],
        "message_length": len(m["body"]),
        "created_at": created_at,
        "edited_at": None if m.get("edited_at") is None else datetime.fromisoformat(m["edited_at"].replace("Z","")),
        "reply_to_id": m.get("reply_to_id"),
        "created_day": created_day,
        "created_hour": created_hour,
    }

def run_etl():
    # Connect DW
    conn = psycopg2.connect(WAREHOUSE_URL)
    ensure_db(conn)

    # 1) Users
    users_url = urljoin(API_BASE_URL + "/", "users")
    users = list(fetch_paginated(users_url))
    if users:
        upsert_users(conn, users)
        print(f"Loaded users: {len(users)}")

    # 2) Chats
    chats_url = urljoin(API_BASE_URL + "/", "chats")
    chats = list(fetch_paginated(chats_url))
    if chats:
        # dim_chats
        upsert_chats(conn, chats)
        print(f"Loaded chats: {len(chats)}")

        # members per chat
        total_members = 0
        for c in chats:
            members_url = urljoin(API_BASE_URL + "/", f"chats/{c['id']}/members")
            members = list(fetch_paginated(members_url))
            if members:
                upsert_chat_members(conn, members)
                total_members += len(members)
        print(f"Loaded chat members: {total_members}")

        # messages per chat
        total_msgs = 0
        for c in chats:
            msgs_url = urljoin(API_BASE_URL + "/", f"chats/{c['id']}/messages")
            msgs_raw = list(fetch_paginated(msgs_url))
            if msgs_raw:
                msgs = [transform_message(m) for m in msgs_raw]
                upsert_messages(conn, msgs)
                total_msgs += len(msgs)
        print(f"Loaded messages: {total_msgs}")

    conn.close()
    print("ETL completed ✔")

if __name__ == "__main__":
    run_etl()
