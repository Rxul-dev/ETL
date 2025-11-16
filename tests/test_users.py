import pytest
from app import models

def test_create_user(client, sample_user_data):
    """Test crear un usuario"""
    response = client.post("/users", json=sample_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["handle"] == sample_user_data["handle"]
    assert data["display_name"] == sample_user_data["display_name"]
    assert "id" in data
    assert "created_at" in data

def test_create_duplicate_user(client, sample_user_data):
    """Test crear usuario duplicado debe fallar"""
    client.post("/users", json=sample_user_data)
    response = client.post("/users", json=sample_user_data)
    assert response.status_code == 409

def test_get_user(client, sample_user_data):
    """Test obtener un usuario por ID"""
    create_response = client.post("/users", json=sample_user_data)
    user_id = create_response.json()["id"]
    
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["handle"] == sample_user_data["handle"]

def test_get_nonexistent_user(client):
    """Test obtener usuario inexistente"""
    response = client.get("/users/99999")
    assert response.status_code == 404

def test_list_users(client, sample_user_data):
    """Test listar usuarios"""
    # Crear algunos usuarios
    for i in range(3):
        user_data = {
            "handle": f"user{i}",
            "display_name": f"User {i}"
        }
        client.post("/users", json=user_data)
    
    response = client.get("/users?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 3

