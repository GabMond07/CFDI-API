from fastapi import APIRouter, Depends
from src.Models.Token import Token, ApiKeyRevokeRequest, RefreshTokenRequest
from src.Models.UserCredentials import UserCredentials
from src.service.login_service import login_user_service
from src.auth import get_current_user, create_api_key, revoke_api_key, refresh_access_token
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(credentials: UserCredentials):
    return await login_user_service(credentials)

@router.post("/generate-api-key")
async def generate_api_key(user: dict = Depends(get_current_user)):
    return await create_api_key(user)

@router.post("/revoke-api-key")
async def revoke_api_key_endpoint(request: ApiKeyRevokeRequest, user: dict = Depends(get_current_user)):
    logger.info(f"Tipo de request: {type(request)}")
    logger.info(f"Body recibido: {request.dict() if hasattr(request, 'dict') else request}")
    logger.info(f"Usuario autenticado: {user}")
    return await revoke_api_key(request.api_key, user)

@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    return await refresh_access_token(request.refresh_token)