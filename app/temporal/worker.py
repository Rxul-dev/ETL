import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from app.temporal.workflows import EtlWorkflow, ProcessChatWorkflow, ProcessChatReactionsWorkflow
from app.temporal import activities as A

async def main():
    target = os.getenv("TEMPORAL_TARGET", "temporal:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    client = await Client.connect(target, namespace=namespace)

    worker = Worker(
        client,
        task_queue="etl-task-queue",
        workflows=[EtlWorkflow, ProcessChatWorkflow, ProcessChatReactionsWorkflow],
        activities=[
            # Extract
            A.extract_users,
            A.extract_chats_and_members,
            A.extract_messages_for_chat,
            # Transform
            A.transform_users,
            A.transform_chats_members,
            A.transform_messages,
            A.transform_reactions,
            # Load
            A.load_dimensions,
            A.load_messages,
            A.load_reactions,
            # Meta / Paginadas
            A.get_chat_meta,
            A.etl_messages_page,
            A.etl_reactions_page,
        ],
    )

    print("ETL Worker started")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())