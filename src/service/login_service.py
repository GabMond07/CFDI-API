from src.Models.UserCredentials import UserCredentials
from src.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta, datetime
from fastapi import HTTPException
from src.event_bus.publisher import publish_event

async def login_user_service(credentials: UserCredentials):
    user = await authenticate_user(credentials.rfc, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect RFC or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user["rfc"], "role_id": user["role_id"]},
        expires_delta=access_token_expires
    )

    await publish_event("login_event", {
        "rfc": user["rfc"],
        "timestamp": datetime.utcnow().isoformat()
    })

    return {"access_token": access_token, "token_type": "bearer"}
