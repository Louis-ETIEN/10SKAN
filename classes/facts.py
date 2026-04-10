from pydantic import BaseModel
from datetime import date

class FactNode(BaseModel):
    concept: str
    label: str
    company: str
    year: str
    filing_type: str
    context: str
    value: float
    period_type: str
    period_start: date
    period_end: date
    period_instant: date