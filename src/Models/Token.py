from pydantic import BaseModel, Field
from typing import Optional, Literal
from pydantic import FileUrl, EmailStr
from datetime import datetime

class Token(BaseModel):
    access_token: str = Field(..., description="Token JWT para autenticación")
    token_type: str = Field(..., description="Tipo de token, debe ser 'bearer'")
    refresh_token: str | None = None

class ApiKeyRevokeRequest(BaseModel):
    api_key: str = Field(..., description="Clave API a revocar")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Token de refresco")