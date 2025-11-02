from __future__ import annotations
from typing import Dict, Any, List
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# ---------- Configuración de política de reintento ----------
retry_policy = RetryPolicy(
    maximum_attempts=5,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
)

# ---------- Importaciones pasadas ----------
with workflow.unsafe.imports_passed_through():
    from app.temporal import activities as A

# ---------- Parámetros globales ----------
HISTORY_SOFT_LIMIT = 5000
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

        # ----- Log de inicio -----
        workflow.logger.info(f" Starting ETL for {len(chats)} chats (page_size={page_size})")

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

        # ----- Fan-out -----
        total_msgs = 0
        total_reacts = 0

        # ----- Utilidad para dividir lotes -----
        def chunks(seq: List[dict], size: int):
            for i in range(0, len(seq), size):
                yield seq[i:i+size]

        # ----- Procesamiento en lotes -----
        for batch in chunks(chats, CHILD_CONCURRENCY):
            handles = []

            # ----- Child workflows -----
            for c in batch:
                cid = c["id"]

                meta_msgs = await workflow.execute_activity(
                    A.get_chat_meta,
                    args=[cid],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )
                total_pages_msgs = int(meta_msgs.get("total_pages", 1))
                total_pages_reacts = total_pages_msgs

                # ----- Mensajes -----
                h_msgs = workflow.execute_child_workflow(
                    ProcessChatWorkflow,
                    args=[cid, total_pages_msgs, page_size],
                    id=f"etl-msgs-{cid}-{workflow.uuid4()}",
                    task_queue="etl-task-queue",
                    retry_policy=retry_policy,
                    execution_timeout=timedelta(hours=2),
                )
                handles.append(("msgs", h_msgs))

                # ----- Reacciones -----
                h_re = workflow.execute_child_workflow(
                    ProcessChatReactionsWorkflow,
                    args=[cid, total_pages_reacts, page_size],
                    id=f"etl-reacts-{cid}-{workflow.uuid4()}",
                    task_queue="etl-task-queue",
                    retry_policy=retry_policy,
                    execution_timeout=timedelta(hours=2),
                )
                handles.append(("reacts", h_re))

            # ----- Espera de resultados -----
            for kind, h in handles:
                inserted = await h
                if kind == "msgs":
                    total_msgs += inserted
                else:
                    total_reacts += inserted
                    
        return {
            "users": len(users),
            "chats": len(chats),
            "members": len(members),
            "messages_loaded": total_msgs,
            "reactions_loaded": total_reacts,
        }