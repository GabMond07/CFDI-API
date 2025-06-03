from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from prisma import Prisma
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configuración para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Clave secreta para JWT (obtenida de la variable de entorno)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1

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

async def create_user(rfc: str, password: str, role: str = "contribuyente", tenant_id: str = None):
    prisma = Prisma()
    await prisma.connect()
    try:
        # Verifica si el RFC ya está registrado
        existing_user = await prisma.user.find_unique(where={"rfc": rfc})
        if existing_user:
            raise ValueError("RFC already registered")
        
        # Hashea la contraseña con bcrypt (incluye un salt único automáticamente)
        hashed_password = pwd_context.hash(password)
        user = await prisma.user.create(
            data={
                "rfc": rfc,
                "hashed_password": hashed_password,
                "role": role,
                "tenant_id": tenant_id
            }
        )
        return user.dict()
    finally:
        await prisma.disconnect()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(rfc: str, password: str):
    user = await get_user(rfc)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

async def clean_expired_tokens():
    """
    Elimina los tokens de la lista negra que ya han expirado usando expires_at.
    """
    prisma = Prisma()
    await prisma.connect()
    try:
        # Eliminar todos los tokens cuya fecha de expiración sea menor que la actual
        await prisma.blacklistedtoken.delete_many(
            where={
                "expires_at": {
                    "lt": datetime.utcnow()
                }
            }
        )
    finally:
        await prisma.disconnect()