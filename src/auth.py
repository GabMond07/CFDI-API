from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
from prisma import Prisma
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clave secreta para JWT (obtenida de la variable de entorno)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# OAuth2 para extraer token de encabezados
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_user(rfc: str):
    prisma = Prisma()
    await prisma.connect()
    try:
        user = await prisma.user.find_unique(where={"rfc": rfc})
        return user.dict() if user else None
    finally:
        await prisma.disconnect()

async def create_user(rfc: str, username: Optional[str], email: Optional[str], password: str, role_id: int = 1):  # role_id=1 por defecto (contribuyente)
    prisma = Prisma()
    await prisma.connect()
    try:
        # Verifica si el RFC ya está registrado
        existing_user = await prisma.user.find_unique(where={"rfc": rfc})
        if existing_user:
            raise ValueError("RFC already registered")
        
        # Hashea la contraseña con bcrypt
        hashed_password = pwd_context.hash(password)
        user = await prisma.user.create(
            data={
                "rfc": rfc,
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "role_id": role_id
            }
        )
        return user.dict()
    finally:
        await prisma.disconnect()

async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Almacenar el token en la tabla AuthToken
    prisma = Prisma()
    await prisma.connect()
    try:
        await prisma.authtoken.create(
            data={
                "token": encoded_jwt,
                "expires_at": expire,
                "user_id": data["sub"]
            }
        )
    finally:
        await prisma.disconnect()
    
    return encoded_jwt

async def authenticate_user(rfc: str, password: str):
    user = await get_user(rfc)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
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

    return user  # ← aquí puedes acceder a user["rfc"], user["role_id"], etc.