import pytest
from app import models

def test_create_chat(client, sample_chat_data, sample_user_data):
    """Test crear un chat"""
    # Crear un usuario primero
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    chat_data = {**sample_chat_data, "members": [user_id]}
    response = client.post("/chats", json=chat_data)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == chat_data["type"]
    assert data["title"] == chat_data["title"]
    assert "id" in data

def test_get_chat(client, sample_chat_data, sample_user_data):
    """Test obtener un chat por ID"""
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    chat_data = {**sample_chat_data, "members": [user_id]}
    create_response = client.post("/chats", json=chat_data)
    chat_id = create_response.json()["id"]
    
    response = client.get(f"/chats/{chat_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == chat_id

def test_get_nonexistent_chat(client):
    """Test obtener chat inexistente"""
    response = client.get("/chats/99999")
    assert response.status_code == 404

def test_list_chats(client, sample_chat_data, sample_user_data):
    """Test listar chats"""
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    # Crear algunos chats
    for i in range(3):
        chat_data = {
            "type": "group",
            "title": f"Chat {i}",
            "members": [user_id]
        }
        client.post("/chats", json=chat_data)
    
    response = client.get("/chats?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 3

def test_list_chat_members(client, sample_chat_data, sample_user_data):
    """Test listar miembros de un chat"""
    user_response = client.post("/users", json=sample_user_data)
    user_id = user_response.json()["id"]
    
    chat_data = {**sample_chat_data, "members": [user_id]}
    create_response = client.post("/chats", json=chat_data)
    chat_id = create_response.json()["id"]
    
    response = client.get(f"/chats/{chat_id}/members")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1

