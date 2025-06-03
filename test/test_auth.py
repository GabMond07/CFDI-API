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

def test_logout_missing_token():
    response = client.post("/auth/logout")
    assert response.status_code == 401
    assert response.json() == {"detail": "Token missing"}

def test_logout_already_blacklisted():
    # Registrar y luego iniciar sesión
    client.post("/auth/register", json={"rfc": "WXYZ010101ABC", "password": "securepassword123"})
    login_response = client.post("/auth/login", json={"rfc": "WXYZ010101ABC", "password": "securepassword123"})
    token = login_response.json()["access_token"]
    
    # Realizar logout una vez
    client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    # Intentar logout de nuevo con el mismo token
    response = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Token already blacklisted"}

def test_clean_expired_tokens():
    # Crear un token con una fecha de expiración en el pasado
    prisma = Prisma()
    prisma.connect()
    try:
        # Generar un token manualmente con exp en el pasado
        expired_token = jwt.encode(
            {
                "sub": "TEST010101EXP",
                "role": "contribuyente",
                "tenant_id": None,
                "exp": int((datetime.utcnow() - timedelta(minutes=1)).timestamp())
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        # Añadir el token a la lista negra
        prisma.blacklistedtoken.create(
            data={
                "token": expired_token,
                "expires_at": datetime.utcnow() - timedelta(minutes=1)
            }
        )
        
        # Generar un token que no ha expirado
        valid_token = jwt.encode(
            {
                "sub": "TEST010101VAL",
                "role": "contribuyente",
                "tenant_id": None,
                "exp": int((datetime.utcnow() + timedelta(minutes=1)).timestamp())
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        # Añadir el token a la lista negra
        prisma.blacklistedtoken.create(
            data={
                "token": valid_token,
                "expires_at": datetime.utcnow() + timedelta(minutes=1)
            }
        )
        
        # Ejecutar la limpieza
        from auth import clean_expired_tokens
        asyncio.run(clean_expired_tokens())
        
        # Verificar que el token expirado fue eliminado
        expired_found = prisma.blacklistedtoken.find_unique(where={"token": expired_token})
        assert expired_found is None
        
        # Verificar que el token válido aún existe
        valid_found = prisma.blacklistedtoken.find_unique(where={"token": valid_token})
        assert valid_found is not None
    finally:
        prisma.disconnect()