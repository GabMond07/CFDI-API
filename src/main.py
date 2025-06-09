from fastapi import FastAPI, HTTPException, Depends, Request, Query
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime, date
from .auth import authenticate_user, create_access_token, create_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import UserCredentials, UserRegister, Token, BatchQueryRequest, BatchQueryResponse
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
            role_id=1  # Rol por defecto
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Genera el token JWT inmediatamente después del registro
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": new_user["rfc"], "role_id": new_user["role_id"]},
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
    access_token = await create_access_token(
        data={"sub": user["rfc"], "role_id": user["role_id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/logout")
async def logout(request: Request):
    """
    Invalida todos los tokens JWT del usuario marcándolos como revocados.
    """
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid token format")
    
    token = token.replace("Bearer ", "")
    
    # Decodificar el token para obtener el RFC del usuario
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_rfc = payload.get("sub")
        if not user_rfc:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Marcar todos los tokens del usuario como revocados
    prisma = Prisma()
    await prisma.connect()
    try:
        # Actualizar todos los tokens del usuario para marcarlos como revocados
        await prisma.authtoken.update_many(
            where={
                "user_id": user_rfc,
                "revoked_at": None  # Solo los que no están revocados
            },
            data={
                "revoked_at": datetime.utcnow()
            }
        )
        return {"message": "Successfully logged out"}
    finally:
        await prisma.disconnect()

@app.get("/datos/tiempo-real")
async def obtener_datos_tiempo_real(limit: int = Query(10, le=50, description="Cantidad máxima de CFDIs recientes")):
    """
    Devuelve los últimos CFDIs emitidos y un resumen del día actual.
    """
    prisma = Prisma()
    await prisma.connect()

    try:
        # Últimos CFDIs emitidos (limit configurable)
        ultimos_cfdis = await prisma.cfdi.find_many(
            order={"issueDate": "desc"},
            take=limit
        )

        # CFDIs emitidos hoy
        hoy = date.today()
        cfdis_hoy = await prisma.cfdi.find_many(
            where={"issueDate": {"equals": hoy}}
        )
        total_emitidos = len(cfdis_hoy)
        suma_total = sum(cfdi.total for cfdi in cfdis_hoy)

        return {
            "ultimosCFDIs": ultimos_cfdis,
            "resumenDelDia": {
                "fecha": hoy,
                "totalEmitidos": total_emitidos,
                "sumaTotal": suma_total
            }
        }

    finally:
        await prisma.disconnect()

@app.post("/datos/batch", response_model=BatchQueryResponse)
async def consultar_en_batch(request: BatchQueryRequest):
    """
    Consulta múltiples conjuntos de datos en modo batch (por lotes).
    """
    resultados = []

    prisma = Prisma()
    await prisma.connect()

    try:
        for filtro in request.filtros:
            resultado = await prisma.cfdi.find_many(where=filtro)
            resultados.append(resultado)
    finally:
        await prisma.disconnect()

    return {"resultados": resultados}
