from fastapi import APIRouter
from src.Models.Token import Token
from src.Models.UserCredentials import UserCredentials
from src.service.login_service import login_user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(credentials: UserCredentials):
    return await login_user_service(credentials)