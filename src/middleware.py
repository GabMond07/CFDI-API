from fastapi import Request, HTTPException
import jwt
from src.auth import SECRET_KEY, ALGORITHM
from src.database import db
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    """
    Middleware para validar tokens JWT o claves de API en las solicitudes.
    Excluye los endpoints de login, registro, logout y rutas públicas.
    Carga permisos del rol para RBAC.
    """
    start_time = datetime.now(timezone.utc)
    
    if request.method == "OPTIONS":
        response = await call_next(request)
        logger.info(f"Middleware (OPTIONS) tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
        return response

    # Excluir rutas públicas
    public_paths = ["/docs", "/openapi.json", "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/logout"]
    if any(request.url.path.startswith(path) for path in public_paths):
        response = await call_next(request)
        logger.info(f"Middleware (ruta pública) tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
        return response
    
    # Obtener token JWT o clave de API
    token = request.headers.get("Authorization")
    api_key = request.headers.get("X-API-Key")

    if not token and not api_key:
        raise HTTPException(status_code=401, detail="Token or API Key missing")

    if token:
        try:
            token = token.replace("Bearer ", "")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    elif api_key:
        # Validar clave de API
        api_key_record = await db.apikey.find_unique(where={"key": api_key})
        if not api_key_record or not api_key_record.active:
            raise HTTPException(status_code=401, detail="Invalid or inactive API Key")
        if api_key_record.expires_at and api_key_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="API Key expired")
        if api_key_record.revoked_at and api_key_record.revoked_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="API Key revoked")
        user = await db.user.find_unique(where={"rfc": api_key_record.user_id}, include={"role": True})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        request.state.user = user.dict()

    response = await call_next(request)
    logger.info(f"Middleware (autenticado) tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return response