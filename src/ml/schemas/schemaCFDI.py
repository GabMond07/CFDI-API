from pydantic import BaseModel

class CFDIInput(BaseModel):
    total: float
    subtotal: float
    payment_form: str
    currency: str
