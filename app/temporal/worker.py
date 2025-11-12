import os
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

# Workflows
from app.temporal.workflows import ( EtlWorkflow, EtlIncrementalWorkflow, BackfillMessagesWorkflow,)

# Activities
from app.temporal import activities as A


async def main() -> None:
    target = os.getenv("TEMPORAL_TARGET", "temporal:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue = os.getenv("ETL_TASK_QUEUE", "etl-task-queue")

    client = await Client.connect(target, namespace=namespace)

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            EtlWorkflow,
            EtlIncrementalWorkflow,
            BackfillMessagesWorkflow,
        ],
        activities=[
            # Extract
            A.extract_users,
            A.extract_chats_and_members,
            A.extract_bookings,
            A.extract_booking_events,
            A.extract_incremental_dimensions,
            # Transform
            A.transform_users,
            A.transform_chats_members,
            A.transform_messages,
            A.transform_reactions,
            A.transform_bookings,
            A.transform_booking_events,
            # Load
            A.load_dimensions,
            A.load_bookings,
            A.load_booking_events,
            # Meta/paginadas (legacy - mantenidas para compatibilidad)
            A.get_chat_meta,
            A.etl_messages_page,
            A.etl_reactions_page,
            A.plan_incremental_message_pages,
            # Nuevas actividades optimizadas (procesan por chat completo)
            A.etl_messages_chat,
            A.etl_reactions_chat,
            # Nuevas actividades optimizadas para bookings (evitan límite de tamaño)
            A.etl_bookings,
            A.etl_booking_events,
            # Watermark
            A.update_watermark,
        ],
        max_concurrent_activities=100,
        max_concurrent_workflow_tasks=50,
    )

    print(f"ETL Worker polling task queue: {task_queue}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())