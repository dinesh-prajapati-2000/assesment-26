from pydantic import BaseModel

class StockUpdateRequest(BaseModel):
    qty: int
    reason: str