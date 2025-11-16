import pytest
from fastapi.testclient import TestClient
from app.websocket_manager import ConnectionManager
import json

def test_websocket_connection(client, db, sample_user_data, sample_chat_data):
    """Test conexión WebSocket básica"""
    # Crear usuario y chat usando la API para que esté en la misma sesión
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    chat_data = {**sample_chat_data, "members": [user_id]}
    chat_response = client.post("/chats", json=chat_data)
    chat_id = chat_response.json()["id"]
    
    # Asegurar que los cambios estén commiteados en la sesión de prueba
    db.commit()
    
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

