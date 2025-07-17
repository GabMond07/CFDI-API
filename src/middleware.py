from fastapi import Request, HTTPException
import jwt
from src.auth import SECRET_KEY, ALGORITHM
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    """
    Middleware para validar tokens JWT en las solicitudes.
    Excluye los endpoints de login, registro y logout.
    Evita consultas a la base de datos para validaciones básicas.
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
    
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    try:
        token = token.replace("Bearer ", "")
        # Decodificar el token (incluye verificación de expiración)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    response = await call_next(request)
    logger.info(f"Middleware (autenticado) tomó {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return response