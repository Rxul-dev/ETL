from __future__ import annotations
from typing import Dict, Any
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

retry_policy = RetryPolicy(
    maximum_attempts=5,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=1),
)

with workflow.unsafe.imports_passed_through():
    from app.temporal import activities as A

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

@workflow.defn
class EtlWorkflow:
    @workflow.run
    async def run(self, page_size: int = 250) -> Dict[str, Any]:
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
        
        await workflow.execute_activity(
            A.load_dimensions,
            args=[users, chats, members],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )
        
        total_msgs = 0 
        
        for c in chats:
            cid = c["id"]
            meta = await workflow.execute_activity(
                A.get_chat_meta,
                args=[cid],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
            total_pages = int(meta.get("total_pages", 1))
            
            inserted = await workflow.execute_child_workflow(
                ProcessChatWorkflow.run,
                args=[cid, total_pages, page_size],
                id=f"etl-chat-{cid}-{workflow.uuid4()}",
                task_queue="etl-task-queue",
                retry_policy=retry_policy,
                execution_timeout=timedelta(hours=1),
            )
            
            total_msgs += inserted
        
        return {
            "users": len(users),
            "chats": len(chats),
            "members": len(members),
            "messages_loaded": total_msgs,
        }