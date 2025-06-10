from fastapi.testclient import TestClient
from src.main import app
from prisma import Prisma
from datetime import datetime, timedelta
import jwt
from src.auth import SECRET_KEY, ALGORITHM

client = TestClient(app)

def test_register_success():
    response = client.post("/auth/register", json={"rfc": "XAXX010101XXX", "password": "securepassword123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_register_duplicate_rfc():
    # Registrar un usuario
    client.post("/auth/register", json={"rfc": "EFGH010101XXX", "password": "securepassword123"})
    # Intentar registrar el mismo RFC
    response = client.post("/auth/register", json={"rfc": "EFGH010101XXX", "password": "differentpassword"})
    assert response.status_code == 400
    assert response.json() == {"detail": "RFC already registered"}

def test_register_invalid_rfc():
    response = client.post("/auth/register", json={"rfc": "INVALIDRFC", "password": "securepassword123"})
    assert response.status_code == 422  # Error de validación de Pydantic

def test_register_short_password():
    response = client.post("/auth/register", json={"rfc": "XAXX010101XXX", "password": "short"})
    assert response.status_code == 422  # Error de validación de Pydantic

def test_login_success():
    # Registrar un usuario primero
    client.post("/auth/register", json={"rfc": "IJKL010101XXX", "password": "securepassword123"})
    # Iniciar sesión con las mismas credenciales
    response = client.post("/auth/login", json={"rfc": "IJKL010101XXX", "password": "securepassword123"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post("/auth/login", json={"rfc": "IJKL010101XXX", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect RFC or password"}

def test_login_missing_fields():
    response = client.post("/auth/login", json={"rfc": "IJKL010101XXX"})
    assert response.status_code == 422  # Error de validación de Pydantic

def test_logout_success():
    # Registrar y luego iniciar sesión para obtener un token
    client.post("/auth/register", json={"rfc": "ABCD010101XYZ", "password": "securepassword123"})
    login_response = client.post("/auth/login", json={"rfc": "ABCD010101XYZ", "password": "securepassword123"})
    token = login_response.json()["access_token"]
    
    # Realizar logout
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"message": "Successfully logged out"}

    # Verificar que el token fue revocado
    prisma = Prisma()
    prisma.connect()
    try:
        auth_token = prisma.authtoken.find_unique(where={"token": token})
        assert auth_token is not None
        assert auth_token.revoked_at is not None
    finally:
        prisma.disconnect()

def test_logout_missing_token():
    response = client.post("/auth/logout")
    assert response.status_code == 401
    assert response.json() == {"detail": "Token missing"}

def test_logout_invalid_token():
    response = client.post("/auth/logout", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}

def test_use_revoked_token():
    # Registrar y luego iniciar sesión
    client.post("/auth/register", json={"rfc": "WXYZ010101ABC", "password": "securepassword123"})
    login_response = client.post("/auth/login", json={"rfc": "WXYZ010101ABC", "password": "securepassword123"})
    token = login_response.json()["access_token"]
    
    # Realizar logout
    client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    
    # Intentar usar el token revocado (si tuvieras un endpoint protegido)
    # Por ahora, verificamos directamente en el middleware
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Token has been revoked"}