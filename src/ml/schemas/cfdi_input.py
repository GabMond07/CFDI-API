from pydantic import BaseModel

class CFDISospechosoInput(BaseModel):
    total: float
    day_of_week: int
    payment_method: str
