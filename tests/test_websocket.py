import pytest
from fastapi.testclient import TestClient
from app.websocket_manager import ConnectionManager
import json

def test_websocket_connection(client, db, sample_user_data, sample_chat_data):
    """Test conexión WebSocket básica"""
    # Crear usuario y chat directamente en la base de datos para asegurar consistencia
    from app import models
    
    # Crear usuario
    user = models.User(handle=sample_user_data["handle"], display_name=sample_user_data["display_name"])
    db.add(user)
    db.flush()
    user_id = user.id
    
    # Crear chat
    chat = models.Chat(type=sample_chat_data["type"], title=sample_chat_data["title"])
    db.add(chat)
    db.flush()
    chat_id = chat.id
    
    # Agregar miembro al chat
    member = models.ChatMember(chat_id=chat_id, user_id=user_id)
    db.add(member)
    db.commit()
    
    # Refrescar para asegurar que los objetos estén actualizados
    db.refresh(chat)
    db.refresh(user)
    
    # Conectar WebSocket
    with client.websocket_connect(f"/ws/chats/{chat_id}?user_id={user_id}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection"
        assert data["status"] == "connected"
        assert data["chat_id"] == chat_id

def test_websocket_nonexistent_chat(client):
    """Test conexión WebSocket a chat inexistente"""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/chats/99999") as websocket:
            pass

def test_websocket_manager_connect():
    """Test ConnectionManager básico"""
    manager = ConnectionManager()
    # Este test verifica que el manager se puede instanciar
    assert manager is not None
    assert manager.active_connections == {}
    assert manager.user_connections == {}

def test_websocket_get_connections(client, sample_user_data, sample_chat_data):
    """Test obtener número de conexiones activas"""
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    chat_data = {**sample_chat_data, "members": [user_id]}
    chat_response = client.post("/chats", json=chat_data)
    chat_id = chat_response.json()["id"]
    
    response = client.get(f"/ws/chats/{chat_id}/connections")
    assert response.status_code == 200
    data = response.json()
    assert "chat_id" in data
    assert "active_connections" in data

