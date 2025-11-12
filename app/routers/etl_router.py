from fastapi import APIRouter
from typing import Dict, Any
from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError
import os
from datetime import datetime

router = APIRouter(prefix="/etl", tags=["etl"])

async def _client() -> Client:
    target = os.getenv("TEMPORAL_TARGET", "temporal:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    return await Client.connect(target, namespace=namespace)

@router.post("/full")
async def launch_full(page_size: int = 250, parallel: int = 8) -> Dict[str, Any]:
    client = await _client()
    wid = f"etl-full-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    handle = await client.start_workflow(
        "EtlWorkflow",
        args=[{"page_size": page_size, "parallel": parallel}],
        id=wid,
        task_queue="etl-task-queue",
    )
    return {"workflow_id": handle.id, "run_id": handle.run_id}

@router.post("/incremental")
async def launch_incremental(page_size: int = 250, parallel: int = 8, since: str | None = None) -> Dict[str, Any]:
    client = await _client()
    wid = f"etl-incr-{datetime.utcnow().strftime('%Y%m%d-%H%M')}"
    cfg = {"page_size": page_size, "parallel": parallel}
    if since:
        cfg["since"] = since
    handle = await client.start_workflow(
        "EtlIncrementalWorkflow",
        args=[cfg],
        id=wid,
        task_queue="etl-task-queue",
    )
    return {"workflow_id": handle.id, "run_id": handle.run_id}

@router.post("/backfill/messages/{chat_id}")
async def backfill_messages(chat_id: int, start_page: int = 1, end_page: int = 1, page_size: int = 250) -> Dict[str, Any]:
    client = await _client()
    wid = f"backfill-msgs-{chat_id}-{start_page}-{end_page}"
    try:
        handle = await client.start_workflow(
            "BackfillMessagesWorkflow",
            args=[{"chat_id": chat_id, "start_page": start_page, "end_page": end_page, "page_size": page_size}],
            id=wid,
            task_queue="etl-task-queue",
        )
    except WorkflowAlreadyStartedError:
        handle = client.get_workflow_handle(wid)
    return {"workflow_id": handle.id, "run_id": handle.run_id}