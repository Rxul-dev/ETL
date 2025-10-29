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
    async def run(self, chat_id: int, page_size: int = 250) -> int:
        """Extrae, transforma y carga mensajes de un chat"""
        msgs = await workflow.execute_activity(
            A.extract_messages_for_chat,
            args=[chat_id, page_size],
            start_to_close_timeout=timedelta(minutes=20),
            retry_policy=retry_policy,
        )

        msgs = await workflow.execute_activity(
            A.transform_messages,
            args=[msgs],
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        inserted = await workflow.execute_activity(
            A.load_messages,
            args=[msgs],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        return inserted
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

            msgs = await workflow.execute_activity(
                A.extract_messages_for_chat,
                args=[cid, page_size],  
                start_to_close_timeout=timedelta(minutes=20),
                retry_policy=retry_policy,
            )

            msgs = await workflow.execute_activity(
                A.transform_messages,
                args=[msgs], 
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )

            inserted = await workflow.execute_activity(
                A.load_messages,
                args=[msgs],  
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )

            total_msgs += inserted

        return {
            "users": len(users),
            "chats": len(chats),
            "members": len(members),
            "messages_loaded": total_msgs,
        }