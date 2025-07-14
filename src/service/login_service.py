from src.Models.UserCredentials import UserCredentials
from src.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta, timezone
from src.event_bus.publisher import publish_event
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def login_user_service(credentials: UserCredentials):
    start_time = datetime.now(timezone.utc)
    logger.info("Iniciando login para RFC: %s", credentials.rfc)
    
    user = await authenticate_user(credentials.rfc, credentials.password)
    if not user:
        logger.error("Autenticación fallida para RFC: %s", credentials.rfc)
        raise HTTPException(status_code=401, detail="Incorrect RFC or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user["rfc"], "role_id": user["role_id"]},
        expires_delta=access_token_expires
    )

    await publish_event("login_event", {
        "rfc": user["rfc"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    logger.info(f"Login completado para RFC: {credentials.rfc} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return {"access_token": access_token, "token_type": "bearer"}