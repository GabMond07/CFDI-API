from datetime import timedelta
from fastapi import HTTPException
from prisma import Prisma
from src.Models.UserRegister import UserRegister
from src.Models.Token import Token
from src.auth import create_user, create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from src.event_bus.publisher import publish_event
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

async def create_user_service(user: UserRegister):
    """
    Registra un nuevo contribuyente y devuelve un token JWT y un refresh token.
    """
    start_time = datetime.now(timezone.utc)
    logger.info("Iniciando registro para RFC: %s", user.rfc)
    
    try:
        new_user = await create_user(
            rfc=user.rfc,
            username=user.username,
            email=user.email,
            password=user.password,
            role_id=1
        )
    except ValueError as e:
        logger.error(f"Error en registro para RFC: {user.rfc}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = await create_access_token(
        data={"sub": new_user["rfc"], "role_id": new_user["role_id"]},
        expires_delta=access_token_expires
    )
    refresh_token = await create_refresh_token(
        data={"sub": new_user["rfc"], "role_id": new_user["role_id"]},
        expires_delta=refresh_token_expires
    )

    await publish_event("register_event", {
        "rfc": new_user["rfc"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    logger.info(f"Registro completado para RFC: {user.rfc} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }