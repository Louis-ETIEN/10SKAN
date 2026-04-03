SCHEMA = {

    "income_statement": {
        "revenue": None,
        "cost_of_revenue": None,
        "gross_profit": None,
        "operating_income": None,
        "net_income": None,
        "weighted_avg_shares_diluted": None,
        "tax_rate": None,
        "income_tax_expense": None,
        "pretax_income": None
    },

    "balance_sheet": {
        "cash": None,
        "accounts_receivable": None,
        "inventory": None,
        "total_assets": None,
        "total_liabilities": None,
        "shareholders_equity": None,
        "debt": None,
        "debt_current": None,
        "debt_noncurrent": None,
        "accounts_payable": None,
        "accrued_liabilities": None,
        "accounts_payable+accrued_liabilities": None,
        "deferred_revenue": None,
        "taxes_payable": None,
    },

    "cashflow_statement": {
        "operating_cash_flow": None,
        "capex": None,
        "free_cash_flow": None
    },

    "derived_metrics": {

        # profitability
        "gross_margin": None,
        "operating_margin": None,
        "net_margin": None,
        "fcf_margin": None,

        # per-share
        "diluted_eps": None,
        "diluted_fcf_per_share": None,

        # returns
        "return_on_assets": None,
        "return_on_equity": None,
        "return_on_invested_capital": None,
        "return_on_operating_capital": None,

        # efficiency
        "asset_turnover": None,

        # cash metrics
        "cash_conversion": None,
        "capex_ratio": None
    },
}

SCHEMA_MM = {

        "share_price": None,
        "shares_outstanding": None,

        "market_cap": None,
        "enterprise_value": None,

        "pe_ratio": None,
        "price_to_sales": None,
        "price_to_book": None,

        "ev_to_revenue": None,
        "ev_to_fcf": None,

        "fcf_yield": None  
}

SCHEMA_MYM = {

    "revenue_cagr": { # 3, 5, 10
        "3y": None,
        "5y": None,
        "10y": None,
    },

    "fcf_cagr": { # 3, 5
        "3y": None,
        "5y": None,
        "10y": None,
    },

    "avg_roe": { # 5, 10
        "3y": None,
        "5y": None,
        "10y": None,
    },

    "operating_margin_change": { # 3
        "3y": None,
        "5y": None,
        "10y": None,
    },

    "share_count_change": { # 3, 5
        "3y": None,
        "5y": None,
        "10y": None,
    },

    "revenue_volatility": { # 10
        "3y": None,
        "5y": None,
        "10y": None,
    },

}