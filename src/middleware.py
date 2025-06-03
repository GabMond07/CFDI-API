from fastapi import Request, HTTPException
import jwt
from .auth import SECRET_KEY, ALGORITHM
from prisma import Prisma

async def auth_middleware(request: Request, call_next):
    """
    Middleware para validar tokens JWT en las solicitudes.
    Excluye los endpoints de login y registro.
    Verifica si el token está en la lista negra.
    """
    if request.url.path in ["/auth/login", "/auth/register", "/auth/logout"]:
        return await call_next(request)

    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    try:
        token = token.replace("Bearer ", "")
        # Verificar si el token está en la lista negra
        prisma = Prisma()
        await prisma.connect()
        try:
            blacklisted = await prisma.blacklistedtoken.find_unique(where={"token": token})
            if blacklisted:
                raise HTTPException(status_code=401, detail="Token has been blacklisted")
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