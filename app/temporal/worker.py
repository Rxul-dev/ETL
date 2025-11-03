import os, json
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from app.temporal.workflows import EtlWorkflow, ProcessChatWorkflow, ProcessChatReactionsWorkflow, BookingFromMessageWorkflow
from app.temporal import activities as A

async def main():
    target = os.getenv("TEMPORAL_TARGET", "temporal:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    client = await Client.connect(target, namespace=namespace)

    worker = Worker(
        client,
        task_queue="etl-task-queue",
        workflows=[EtlWorkflow, ProcessChatWorkflow, ProcessChatReactionsWorkflow, BookingFromMessageWorkflow],
        activities=[
            # Extract
            A.extract_users,
            A.extract_chats_and_members,
            A.extract_messages_for_chat,
            A.extract_bookings,
            A.extract_booking_events,

            # Transform
            A.transform_users,
            A.transform_chats_members,
            A.transform_messages,
            A.transform_reactions,
            A.transform_bookings,
            A.transform_booking_events,

            # Load
            A.load_dimensions,
            A.load_messages,
            A.load_reactions,
            A.load_bookings,
            A.load_booking_events,

            # Meta / paginadas
            A.get_chat_meta,
            A.etl_messages_page,
            A.etl_reactions_page,

            # Booking creation 
            A.parse_booking_message,
            A.create_booking_from_message,
            A.send_booking_confirmation,
        ],
    )

    print("ETL Worker started")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())