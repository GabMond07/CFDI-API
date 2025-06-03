from pydantic import BaseModel, Field

class UserCredentials(BaseModel):
    rfc: str
    password: str

class UserRegister(BaseModel):
    rfc: str = Field(..., pattern="^[A-Z&Ñ]{3,4}[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[A-Z0-9]{3}$")  # Valida formato de RFC
    password: str = Field(..., min_length=8)  # Contraseña mínima de 8 caracteres

class Token(BaseModel):
    access_token: str
    token_type: str