from pydantic import BaseModel, Field

class UserCredentials(BaseModel):
    rfc: str = Field(..., description="RFC del usuario para autenticación")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")

class UserRegister(BaseModel):
    rfc: str = Field(
        ...,
        pattern="^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$",
        description="RFC del usuario con formato válido (ej. XAXX010101XXX)"
    )
    password: str = Field(..., min_length=8, description="Contraseña mínima de 8 caracteres")

class Token(BaseModel):
    access_token: str = Field(..., description="Token JWT para autenticación")
    token_type: str = Field(..., description="Tipo de token, debe ser 'bearer'")