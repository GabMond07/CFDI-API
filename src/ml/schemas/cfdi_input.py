from pydantic import BaseModel

class CFDISospechosoInput(BaseModel):
    total: float
    day_of_week: int  # 0 = lunes, 6 = domingo
    payment_method: str
