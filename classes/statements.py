from pydantic import BaseModel
from facts import FactNode
from datetime import date
from typing import Dict

class Statement(BaseModel):
    company: str
    year: str
    period_type: str
    period_start: date
    period_end: date
    period_instant: date

    root: FactNode
    fact_map: Dict[str, FactNode]


