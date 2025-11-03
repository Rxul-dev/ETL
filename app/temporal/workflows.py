from __future__ import annotations
from typing import Dict, Any, List
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# ---------- Política de reintento ----------
retry_policy = RetryPolicy(
    maximum_attempts=5,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
)


with workflow.unsafe.imports_passed_through():
    from app.temporal import activities as A

# ---------- Parámetros globales ----------HISTORY_SOFT_LIMIT = 5000  
CHILD_CONCURRENCY = 8

# ---------- Workflow para procesar mensajes ----------
@workflow.defn
class ProcessChatWorkflow:
    @workflow.run
    async def run(self, chat_id: int, total_pages: int, page_size: int = 250) -> int:
        total_inserted = 0
        for page in range(1, total_pages + 1):
            inserted = await workflow.execute_activity(
                A.etl_messages_page,
                args=[chat_id, page, page_size],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            total_inserted += inserted
        return total_inserted

# ---------- Workflow para procesar reacciones ----------
@workflow.defn
class ProcessChatReactionsWorkflow:
    @workflow.run
    async def run(self, chat_id: int, total_pages: int, page_size: int = 250) -> int:
        total_inserted = 0
        for page in range(1, total_pages + 1):
            inserted = await workflow.execute_activity(
                A.etl_reactions_page,
                args=[chat_id, page, page_size],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            total_inserted += inserted
        return total_inserted

# ---------- Workflow para crear booking desde mensaje ----------
@workflow.defn
class BookingFromMessageWorkflow:
    @workflow.run
    async def run(self, message: dict) -> int:
        booking_id = await workflow.execute_activity(
            A.create_booking_from_message,
            args=[message],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )
        await workflow.execute_activity(
            A.send_booking_confirmation,
            args=[message["chat_id"], booking_id],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )
        return booking_id

# ---------- Workflow principal ETL ----------
@workflow.defn
class EtlWorkflow:
    @workflow.run
    async def run(self, page_size: int = 250) -> Dict[str, Any]:
        # ----- Extract -----
        users = await workflow.execute_activity(
            A.extract_users,
            args=[page_size],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )
        chats, members = await workflow.execute_activity(
            A.extract_chats_and_members,
            args=[page_size],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        workflow.logger.info(f"Starting ETL for {len(chats)} chats (page_size={page_size})")

        # ----- Transform -----
        users = await workflow.execute_activity(
            A.transform_users,
            args=[users],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )
        chats, members = await workflow.execute_activity(
            A.transform_chats_members,
            args=[chats, members],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        # ----- Load dimensiones -----
        await workflow.execute_activity(
            A.load_dimensions,
            args=[users, chats, members],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        # ----- Fan-out: mensajes y reacciones -----
        total_msgs = 0
        total_reacts = 0

        def chunks(seq: List[dict], size: int):
            for i in range(0, len(seq), size):
                yield seq[i:i+size]

        for batch in chunks(chats, CHILD_CONCURRENCY):
            handles = []

            for c in batch:
                cid = c["id"]

                meta_msgs = await workflow.execute_activity(
                    A.get_chat_meta,
                    args=[cid],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )
                total_pages_msgs = int(meta_msgs.get("total_pages", 1))

                # Mensajes
                h_msgs = workflow.execute_child_workflow(
                    ProcessChatWorkflow,
                    args=[cid, total_pages_msgs, page_size],
                    id=f"etl-msgs-{cid}-{workflow.uuid4()}",
                    task_queue="etl-task-queue",
                    retry_policy=retry_policy,
                    execution_timeout=timedelta(hours=2),
                )
                handles.append(("msgs", h_msgs))

                h_reacts = workflow.execute_child_workflow(
                    ProcessChatReactionsWorkflow,
                    args=[cid, total_pages_msgs, page_size],
                    id=f"etl-reacts-{cid}-{workflow.uuid4()}",
                    task_queue="etl-task-queue",
                    retry_policy=retry_policy,
                    execution_timeout=timedelta(hours=2),
                )
                handles.append(("reacts", h_reacts))

            for kind, h in handles:
                inserted = await h
                if kind == "msgs":
                    total_msgs += inserted
                else:
                    total_reacts += inserted
                    
        bookings_loaded = None
        booking_events_loaded = None

        if hasattr(A, "extract_bookings") and hasattr(A, "transform_bookings") and hasattr(A, "load_bookings"):
            bookings = await workflow.execute_activity(
                A.extract_bookings,
                args=[page_size],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            bookings = await workflow.execute_activity(
                A.transform_bookings,
                args=[bookings],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            bookings_loaded = await workflow.execute_activity(
                A.load_bookings,
                args=[bookings],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

        if hasattr(A, "extract_booking_events") and hasattr(A, "transform_booking_events") and hasattr(A, "load_booking_events"):
            booking_events = await workflow.execute_activity(
                A.extract_booking_events,
                args=[page_size],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            booking_events = await workflow.execute_activity(
                A.transform_booking_events,
                args=[booking_events],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            booking_events_loaded = await workflow.execute_activity(
                A.load_booking_events,
                args=[booking_events],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

        # ----- Resultado -----
        result: Dict[str, Any] = {
            "users": len(users),
            "chats": len(chats),
            "members": len(members),
            "messages_loaded": total_msgs,
            "reactions_loaded": total_reacts,
        }
        if bookings_loaded is not None:
            result["bookings_loaded"] = bookings_loaded
        if booking_events_loaded is not None:
            result["booking_events_loaded"] = booking_events_loaded
        return result