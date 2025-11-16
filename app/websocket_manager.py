from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
from prometheus_client import Counter, Gauge
import json
import logging

logger = logging.getLogger(__name__)

# Métricas de Prometheus para WebSocket
websocket_connections_total = Counter(
    'websocket_connections_total',
    'Total number of WebSocket connections',
    ['status']
)

websocket_messages_sent_total = Counter(
    'websocket_messages_sent_total',
    'Total number of messages sent via WebSocket',
    ['chat_id']
)

websocket_active_connections = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections',
    ['chat_id']
)

class ConnectionManager:
    """Gestiona las conexiones WebSocket por chat"""
    
    def __init__(self):
        # chat_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # user_id -> Set[WebSocket] (para tracking por usuario)
        self.user_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int = None):
        """Conecta un WebSocket a un chat específico"""
        await websocket.accept()
        
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()
        
        self.active_connections[chat_id].add(websocket)
        websocket_connections_total.labels(status='connected').inc()
        websocket_active_connections.labels(chat_id=str(chat_id)).inc()
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected to chat {chat_id} (user: {user_id})")
    
    def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int = None):
        """Desconecta un WebSocket de un chat"""
        if chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
            websocket_active_connections.labels(chat_id=str(chat_id)).dec()
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        websocket_connections_total.labels(status='disconnected').inc()
        logger.info(f"WebSocket disconnected from chat {chat_id} (user: {user_id})")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Envía un mensaje a una conexión específica"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_chat(self, message: dict, chat_id: int):
        """Envía un mensaje a todos los clientes conectados a un chat"""
        if chat_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[chat_id]:
            try:
                await connection.send_json(message)
                websocket_messages_sent_total.labels(chat_id=str(chat_id)).inc()
            except Exception as e:
                logger.error(f"Error broadcasting to chat {chat_id}: {e}")
                disconnected.add(connection)
        
        # Limpiar conexiones desconectadas
        for conn in disconnected:
            self.active_connections[chat_id].discard(conn)
            websocket_active_connections.labels(chat_id=str(chat_id)).dec()
    
    def get_chat_connections_count(self, chat_id: int) -> int:
        """Obtiene el número de conexiones activas en un chat"""
        return len(self.active_connections.get(chat_id, set()))

# Instancia global del manager
manager = ConnectionManager()

