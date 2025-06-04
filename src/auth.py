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
ACCESS_TOKEN_EXPIRE_MINUTES = 60

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

async def create_user(rfc: str, password: str, role_id: int = 1):  # role_id=1 por defecto (contribuyente)
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