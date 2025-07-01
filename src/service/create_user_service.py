from datetime import timedelta
from fastapi import HTTPException
from prisma import Prisma
from src.Models.UserRegister import UserRegister
from src.Models.Token import Token
from src.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_user

async def create_user_service(user: UserRegister):
    """
    Registra un nuevo contribuyente y devuelve un token JWT.
    """
    try:
        new_user = await create_user(
            rfc=user.rfc,
            username=user.username,
            email=user.email,
            password=user.password,
            role_id=1
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": new_user["rfc"], "role_id": new_user["role_id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
