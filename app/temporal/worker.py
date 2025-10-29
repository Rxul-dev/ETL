import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from app.temporal.workflows import EtlWorkflow
from app.temporal import activities

async def main():
    target = os.getenv("TEMPORAL_TARGET", "temporal:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    client = await Client.connect(target, namespace=namespace)
    worker = Worker(
        client,
        task_queue="etl-task-queue",
        workflows=[EtlWorkflow],
        activities=[
            activities.extract_users,
            activities.extract_chats_and_members,
            activities.extract_messages_for_chat,
            activities.transform_users,
            activities.transform_chats_members,
            activities.transform_messages,
            activities.load_dimensions,
            activities.load_messages,
        ],
    )
    print("ETL Worker started")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())