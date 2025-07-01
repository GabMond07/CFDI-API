from fastapi import APIRouter, HTTPException
from src.Models.UserRegister import UserRegister
from src.Models.Token import Token
from src.service.create_user_service import create_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
async def register(user: UserRegister):
    try:
        return await create_user_service(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
