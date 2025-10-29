from fastapi import APIRouter
from temporalio.client import Client
from app.temporal.workflows import EtlWorkflow
import os, time

router = APIRouter(prefix="/etl", tags=["etl"])

TEMPORAL_TARGET = os.getenv("TEMPORAL_TARGET", "temporal:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")

async def get_temporal_client() -> Client:
    """Crea o reutiliza un cliente Temporal."""
    return await Client.connect(TEMPORAL_TARGET, namespace=TEMPORAL_NAMESPACE)

@router.post("", status_code=202)
async def start_etl(page_size: int = 250):
    """
    Inicia el workflow ETL en Temporal y devuelve su identificador.
    """
    client = await get_temporal_client()
    workflow_id = f"etl-{int(time.time())}"
    handle = await client.start_workflow(
        EtlWorkflow.run,
        page_size,
        id=workflow_id,
        task_queue="etl-task-queue",
    )
    return {"workflow_id": handle.id, "run_id": handle.run_id}

@router.get("/{workflow_id}")
async def get_etl_status(workflow_id: str):
    """
    Consulta el estado del workflow ETL y su resultado (si terminó).
    """
    client = await get_temporal_client()
    handle = client.get_workflow_handle(workflow_id)
    info = await handle.describe()

    result = None
    if info.status.name == "COMPLETED":
        try:
            result = await handle.result()
        except Exception:
            pass

    return {
        "workflow_id": workflow_id,
        "status": info.status.name,
        "result": result,
    }