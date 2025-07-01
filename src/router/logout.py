from fastapi import APIRouter, Request
from src.service.logout_service import logout_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/logout")
async def logout(request: Request):
    return await logout_service(request)
