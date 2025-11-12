from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import timedelta
import asyncio
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

PARALLEL = 8
CONTINUE_EVERY = 5000 


def _chunks(seq: List[Any], size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


async def _map_activities(
    items: List[Any],
    fn_name: str,
    args_builder,
    timeout: timedelta,
    parallel: int = PARALLEL,
) -> List[Any]:
    """
    Ejecuta actividades en paralelo con manejo robusto de errores.
    Si una actividad falla o se cuelga, las demás continúan.
    """
    results: List[Any] = []
    for batch in _chunks(items, parallel):
        handles = [
            workflow.start_activity(
                getattr(A, fn_name),
                args=args_builder(item),
                start_to_close_timeout=timeout,
                retry_policy=retry_policy,
            )
            for item in batch
        ]
        # Esperar todas las actividades del batch en paralelo
        # Temporal maneja el paralelismo, pero esperamos todas juntas
        # para que si una falla, las demás continúen
        for h in handles:
            try:
                result = await h
                results.append(result)
            except Exception as e:
                # Si una actividad falla, registramos el error pero continuamos
                # con las demás actividades del batch
                workflow.logger.warning(f"Activity failed: {e}")
                results.append(None)  # Valor por defecto para actividades fallidas
    return results


@workflow.defn
class EtlWorkflow:
    @workflow.run
    async def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        page_size = int(config.get("page_size", 250))
        parallel = int(config.get("parallel", PARALLEL))

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
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        # REFACTORIZADO: Procesar por chat completo en lugar de página por página
        # Esto reduce drásticamente el número de actividades y eventos en el historial
        chat_ids = [c["id"] for c in chats]
        
        # Procesar mensajes: una actividad por chat (no por página)
        msg_results = await _map_activities(
            chat_ids,
            "etl_messages_chat",
            args_builder=lambda cid: [cid, page_size],
            timeout=timedelta(minutes=30),  # Timeout más largo para chats grandes
            parallel=parallel,
        )
        total_msgs = sum(int(r.get("messages_loaded", 0) if isinstance(r, dict) else 0) for r in msg_results)
        
        # Procesar reacciones: una actividad por chat (no por página)
        react_results = await _map_activities(
            chat_ids,
            "etl_reactions_chat",
            args_builder=lambda cid: [cid, page_size],
            timeout=timedelta(minutes=30),  # Timeout más largo para chats grandes
            parallel=parallel,
        )
        # Manejar resultados None (actividades fallidas) de forma segura
        total_reacts = sum(
            int(r.get("reactions_loaded", 0) if isinstance(r, dict) else 0) 
            for r in react_results 
            if r is not None
        )

        result: Dict[str, Any] = {
            "users": len(users),
            "chats": len(chats),
            "members": len(members),
            "messages_loaded": total_msgs,
            "reactions_loaded": total_reacts,
        }

        # REFACTORIZADO: Usar etl_bookings que procesa directamente sin retornar todos los datos
        # Esto evita el error "Complete result exceeds size limit" de Temporal
        if hasattr(A, "etl_bookings"):
            bookings_result = await workflow.execute_activity(
                A.etl_bookings,
                args=[page_size],
                start_to_close_timeout=timedelta(minutes=30),  # Timeout más largo para grandes volúmenes
                retry_policy=retry_policy,
            )
            result["bookings_loaded"] = int(bookings_result.get("bookings_loaded", 0) if isinstance(bookings_result, dict) else 0)
        elif all(hasattr(A, n) for n in ("extract_bookings", "transform_bookings", "load_bookings")):
            # Fallback al método antiguo si etl_bookings no existe
            bookings = await workflow.execute_activity(
                A.extract_bookings,
                args=[page_size],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            bookings = await workflow.execute_activity(
                A.transform_bookings,
                args=[bookings],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            loaded = await workflow.execute_activity(
                A.load_bookings,
                args=[bookings],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
            result["bookings_loaded"] = int(loaded or 0)

        # REFACTORIZADO: Usar etl_booking_events que procesa directamente sin retornar todos los datos
        if hasattr(A, "etl_booking_events"):
            events_result = await workflow.execute_activity(
                A.etl_booking_events,
                args=[page_size],
                start_to_close_timeout=timedelta(minutes=30),  # Timeout más largo para grandes volúmenes
                retry_policy=retry_policy,
            )
            result["booking_events_loaded"] = int(events_result.get("events_loaded", 0) if isinstance(events_result, dict) else 0)
        elif all(
            hasattr(A, n)
            for n in ("extract_booking_events", "transform_booking_events", "load_booking_events")
        ):
            # Fallback al método antiguo si etl_booking_events no existe
            bevents = await workflow.execute_activity(
                A.extract_booking_events,
                args=[page_size],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )
            bevents = await workflow.execute_activity(
                A.transform_booking_events,
                args=[bevents],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry_policy,
            )
            loaded = await workflow.execute_activity(
                A.load_booking_events,
                args=[bevents],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
            )
            result["booking_events_loaded"] = int(loaded or 0)

        return result


@workflow.defn
class EtlIncrementalWorkflow:
    @workflow.run
    async def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        page_size = int(config.get("page_size", 250))
        parallel = int(config.get("parallel", PARALLEL))
        since: Optional[str] = config.get("since", "watermark:auto")

        users, chats, members = await workflow.execute_activity(
            A.extract_incremental_dimensions,
            args=[since, page_size],
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
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        # REFACTORIZADO: Procesar por chat completo en lugar de página por página
        # Esto reduce drásticamente el número de actividades y eventos en el historial
        chat_ids = [c["id"] for c in chats]
        
        # Procesar mensajes: una actividad por chat (no por página)
        msg_results = await _map_activities(
            chat_ids,
            "etl_messages_chat",
            args_builder=lambda cid: [cid, page_size],
            timeout=timedelta(minutes=30),  # Timeout más largo para chats grandes
            parallel=parallel,
        )
        total_msgs = sum(int(r.get("messages_loaded", 0) if isinstance(r, dict) else 0) for r in msg_results)
        
        # Procesar reacciones: una actividad por chat (no por página)
        react_results = await _map_activities(
            chat_ids,
            "etl_reactions_chat",
            args_builder=lambda cid: [cid, page_size],
            timeout=timedelta(minutes=30),  # Timeout más largo para chats grandes
            parallel=parallel,
        )
        # Manejar resultados None (actividades fallidas) de forma segura
        total_reacts = sum(
            int(r.get("reactions_loaded", 0) if isinstance(r, dict) else 0) 
            for r in react_results 
            if r is not None
        )

        # Actualizar watermarks específicos por entidad
        now_iso = workflow.now().isoformat()
        await workflow.execute_activity(
            A.update_watermark,
            args=["users", now_iso],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )
        await workflow.execute_activity(
            A.update_watermark,
            args=["chats", now_iso],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )
        await workflow.execute_activity(
            A.update_watermark,
            args=["members", now_iso],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )
        await workflow.execute_activity(
            A.update_watermark,
            args=["messages", now_iso],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )

        return {
            "users": len(users),
            "chats": len(chats),
            "members": len(members),
            "messages_loaded": total_msgs,
            "reactions_loaded": total_reacts,
        }


@workflow.defn
class BackfillMessagesWorkflow:
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        chat_id = int(params["chat_id"])
        page_size = int(params.get("page_size", 250))
        start_page = int(params.get("start_page", 1))
        end_page = int(params.get("end_page", start_page))

        pages = [{"chat_id": chat_id, "page": p} for p in range(start_page, end_page + 1)]
        msg_inserted_list = await _map_activities(
            pages,
            "etl_messages_page",
            args_builder=lambda t: [t["chat_id"], t["page"], page_size],
            timeout=timedelta(minutes=5),
            parallel=min(PARALLEL, 4),
        )
        react_inserted_list = await _map_activities(
            pages,
            "etl_reactions_page",
            args_builder=lambda t: [t["chat_id"], t["page"], page_size],
            timeout=timedelta(minutes=5),
            parallel=min(PARALLEL, 4),
        )
        return {
            "chat_id": chat_id,
            "messages_loaded": sum(int(x or 0) for x in msg_inserted_list),
            "reactions_loaded": sum(int(x or 0) for x in react_inserted_list),
        }