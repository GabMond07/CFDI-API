from fastapi import Request, HTTPException
import jwt
from .auth import SECRET_KEY, ALGORITHM
from prisma import Prisma
from datetime import datetime, timezone

async def auth_middleware(request: Request, call_next):
    """
    Middleware para validar tokens JWT en las solicitudes.
    Excluye los endpoints de login y registro.
    Verifica si el token está revocado o ha expirado.
    """
    # Excluir rutas de documentación y autenticación pública
    if request.url.path in ["/docs", "/openapi.json", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/logout"]:
        return await call_next(request)
    
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    try:
        token = token.replace("Bearer ", "")
        # Verificar si el token existe, está revocado o ha expirado
        prisma = Prisma()
        await prisma.connect()
        try:
            auth_token = await prisma.authtoken.find_unique(where={"token": token})
            if not auth_token:
                raise HTTPException(status_code=401, detail="Invalid token")
            if auth_token.revoked_at:
                raise HTTPException(status_code=401, detail="Token has been revoked")
            if auth_token.expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Token has expired")
        finally:
            await prisma.disconnect()

        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return await call_next(request)