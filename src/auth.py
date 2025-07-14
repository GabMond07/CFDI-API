from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from src.database import db  # Importar singleton
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clave secreta para JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# OAuth2 para extraer token de encabezados
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    start_time = datetime.now(timezone.utc)
    result = pwd_context.verify(plain_password, hashed_password)
    logger.info(f"Verificación de contraseña tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return result

async def get_user(rfc: str):
    start_time = datetime.now(timezone.utc)
    user = await db.user.find_unique(where={"rfc": rfc})
    logger.info(f"Consulta de usuario tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return user.dict() if user else None

async def create_user(rfc: str, username: Optional[str], email: Optional[str], password: str, role_id: int = 1):
    start_time = datetime.now(timezone.utc)
    existing_user = await db.user.find_unique(where={"rfc": rfc})
    if existing_user:
        raise ValueError("RFC already registered")
    
    hashed_password = pwd_context.hash(password)
    user = await db.user.create(
        data={
            "rfc": rfc,
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role_id": role_id
        }
    )
    logger.info(f"Creación de usuario tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return user.dict()

async def create_access_token(data: dict, expires_delta: timedelta = None):
    start_time = datetime.now(timezone.utc)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    await db.authtoken.create(
        data={
            "token": encoded_jwt,
            "expires_at": expire,
            "user_id": data["sub"]
        }
    )
    logger.info(f"Creación de token tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return encoded_jwt

async def authenticate_user(rfc: str, password: str):
    start_time = datetime.now(timezone.utc)
    user = await get_user(rfc)
    if not user:
        logger.error(f"Usuario no encontrado: {rfc}")
        return False
    if not verify_password(password, user["hashed_password"]):
        logger.error(f"Contraseña incorrecta para RFC: {rfc}")
        return False
    logger.info(f"Autenticación de usuario tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    start_time = datetime.now(timezone.utc)
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token inválido o expirado",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        rfc = payload.get("sub")
        if rfc is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = await get_user(rfc)
    if user is None:
        raise credentials_exception
    logger.info(f"Obtención de usuario actual tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return user