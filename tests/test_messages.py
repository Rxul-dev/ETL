import pytest
from app import models

def test_send_message(client, sample_user_data, sample_chat_data, sample_message_data):
    """Test enviar un mensaje"""
    # Crear usuario y chat
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    chat_data = {**sample_chat_data, "members": [user_id]}
    chat_response = client.post("/chats", json=chat_data)
    chat_id = chat_response.json()["id"]
    
    message_data = {**sample_message_data, "sender_id": user_id}
    response = client.post(f"/chats/{chat_id}/messages", json=message_data)
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == message_data["body"]
    assert data["chat_id"] == chat_id
    assert data["sender_id"] == user_id

def test_send_message_nonexistent_chat(client, sample_message_data):
    """Test enviar mensaje a chat inexistente"""
    response = client.post("/chats/99999/messages", json=sample_message_data)
    assert response.status_code == 404

def test_list_messages(client, sample_user_data, sample_chat_data, sample_message_data):
    """Test listar mensajes de un chat"""
    # Crear usuario y chat
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    chat_data = {**sample_chat_data, "members": [user_id]}
    chat_response = client.post("/chats", json=chat_data)
    chat_id = chat_response.json()["id"]
    
    # Enviar algunos mensajes
    message_data = {**sample_message_data, "sender_id": user_id}
    for i in range(3):
        msg = {**message_data, "body": f"Message {i}"}
        client.post(f"/chats/{chat_id}/messages", json=msg)
    
    response = client.get(f"/chats/{chat_id}/messages?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 3

