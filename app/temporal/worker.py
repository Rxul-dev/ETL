import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from app.temporal.workflows import EtlWorkflow, ProcessChatWorkflow
from app.temporal import activities as A

async def main():
    target = os.getenv("TEMPORAL_TARGET", "temporal:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    client = await Client.connect(target, namespace=namespace)

    worker = Worker(
        client,
        task_queue="etl-task-queue",
        workflows=[EtlWorkflow, ProcessChatWorkflow],
        activities=[
            A.extract_users,
            A.extract_chats_and_members,
            A.extract_messages_for_chat,
            A.transform_users,
            A.transform_chats_members,
            A.transform_messages,
            A.load_dimensions,
            A.load_messages,
            A.get_chat_meta,
            A.etl_messages_page,
        ],
    )
    print("ETL Worker started")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())