from statements import IncomeStatement, BalanceSheet, CashflowStatement, DerivedMetrics
from pydantic import BaseModel

class Filing(BaseModel):
    company: str
    year: str
    cik: str
    ticker: str
    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    cashflow_statement: CashflowStatement
    derived_metrics: DerivedMetrics