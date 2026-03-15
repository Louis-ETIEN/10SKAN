SCHEMA = {

    "income_statement": {
        "revenue": None,
        "cost_of_revenue": None,
        "gross_profit": None,
        "operating_income": None,
        "net_income": None
    },

    "balance_sheet": {
        "cash": None,
        "accounts_receivable": None,
        "inventory": None,
        "total_assets": None,
        "total_liabilities": None,
        "shareholders_equity": None
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

        # returns
        "return_on_assets": None,
        "return_on_equity": None,

        # efficiency
        "asset_turnover": None,

        # cash metrics
        "cash_conversion": None,
        "capex_ratio": None
    },

    "market_metrics": {

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
}

