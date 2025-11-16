from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.websocket_manager import manager
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/chats/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, user_id: int = Query(None)):
    """
    Endpoint WebSocket para escuchar mensajes en tiempo real de un chat.
    
    Parámetros:
    - chat_id: ID del chat al que conectarse
    - user_id: ID del usuario (opcional, para tracking)
    """
    # Verificar que el chat existe
    db = next(get_db())
    try:
        # Expirar objetos para forzar recarga desde la base de datos
        db.expire_all()
        # Usar query en lugar de get para asegurar que busca en la base de datos
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            await websocket.close(code=1008, reason="Chat not found")
            return
        
        # Verificar que el usuario es miembro del chat (si se proporciona user_id)
        if user_id:
            member = db.query(models.ChatMember).filter_by(
                chat_id=chat_id, 
                user_id=user_id
            ).first()
            if not member:
                await websocket.close(code=1008, reason="User is not a member of this chat")
                return
        
        # Conectar el WebSocket
        await manager.connect(websocket, chat_id, user_id)
        
        try:
            # Enviar mensaje de bienvenida
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "chat_id": chat_id,
                "message": "Connected to chat"
            })
            
            # Mantener la conexión abierta y escuchar mensajes
            while True:
                # Opcional: recibir mensajes del cliente (ping/pong, etc.)
                try:
                    data = await websocket.receive_text()
                    # Procesar mensajes del cliente si es necesario
                    try:
                        message = json.loads(data)
                        if message.get("type") == "ping":
                            await websocket.send_json({"type": "pong"})
                    except json.JSONDecodeError:
                        pass
                except WebSocketDisconnect:
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected from chat {chat_id}")
        finally:
            manager.disconnect(websocket, chat_id, user_id)
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    finally:
        db.close()

@router.get("/ws/chats/{chat_id}/connections")
async def get_chat_connections(chat_id: int):
    """Obtiene el número de conexiones activas en un chat"""
    count = manager.get_chat_connections_count(chat_id)
    return {"chat_id": chat_id, "active_connections": count}

