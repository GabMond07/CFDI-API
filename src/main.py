from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime
from .auth import authenticate_user, create_access_token, create_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import UserCredentials, UserRegister, Token
from .middleware import auth_middleware
from prisma import Prisma
import jwt
from .auth import SECRET_KEY, ALGORITHM

app = FastAPI(title="Web API Fiscal")

# Añade el middleware de autenticación
app.middleware("http")(auth_middleware)

# OAuth2 para manejar el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@app.post("/auth/register", response_model=Token)
async def register(user: UserRegister):
    """
    Registra un nuevo contribuyente y devuelve un token JWT.
    """
    try:
        # Crea el usuario en la base de datos
        new_user = await create_user(
            rfc=user.rfc,
            password=user.password,
            role="contribuyente"  # Rol por defecto
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Genera el token JWT inmediatamente después del registro
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user["rfc"], "role": new_user["role"], "tenant_id": new_user["tenant_id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserCredentials):
    """
    Autentica al contribuyente y devuelve un token JWT.
    """
    user = await authenticate_user(credentials.rfc, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect RFC or password")
    
    # Genera el token JWT con información del usuario
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["rfc"], "role": user["role"], "tenant_id": user["tenant_id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/logout")
async def logout(request: Request):
    """
    Invalida el token JWT añadiéndolo a la lista negra.
    """
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    token = token.replace("Bearer ", "")
    
    # Decodificar el token para obtener la fecha de expiración
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False, "verify_exp": False})
        exp = payload.get("exp")
        if not exp:
            raise HTTPException(status_code=400, detail="Token has no expiration")
        expires_at = datetime.utcfromtimestamp(exp)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    # Añadir el token a la lista negra
    prisma = Prisma()
    await prisma.connect()
    try:
        # Verificar si el token ya está en la lista negra
        existing = await prisma.blacklistedtoken.find_unique(where={"token": token})
        if existing:
            raise HTTPException(status_code=400, detail="Token already blacklisted")
        
        # Añadir el token con su fecha de expiración
        await prisma.blacklistedtoken.create(
            data={
                "token": token,
                "expires_at": expires_at
            }
        )
        return {"message": "Successfully logged out"}
    finally:
        await prisma.disconnect()