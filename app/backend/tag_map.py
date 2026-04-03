TAG_MAP = {

"income_statement": {

    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "SalesRevenueServicesNet",
        "SalesRevenueNetOfReturnsAndAllowances",
        "RevenuesNetOfInterestExpense",
        "OperatingRevenue",
        "TotalRevenuesNetOfInterestExpense"
    ],

    "cost_of_revenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfGoodsSold",
        "CostOfSales",
        "CostOfServices",
        "CostOfProductsSold",
        "CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization"
    ],

    "gross_profit": [
        "GrossProfit"
    ],

    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromOperations",
        "OperatingProfitLoss",
        "IncomeFromOperations",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "OperatingIncome",
        "OperatingProfit",
        "OperatingIncomeLossBeforeDepreciationAmortization"
    ],

    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
        "NetIncomeLossAvailableToCommonStockholdersDiluted",
        "IncomeLossFromContinuingOperations"
    ],

    "weighted_avg_shares_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingDiluted",
        "WeightedAverageNumberOfShareOutstandingDiluted",
        "WeightedAverageNumberOfSharesDiluted",
        "WeightedAverageSharesDiluted",
        "DilutedWeightedAverageSharesOutstanding",
        "WeightedAverageNumberOfCommonSharesOutstandingDiluted"
    ],

    "tax_rate": [
        "EffectiveIncomeTaxRateContinuingOperations"
    ],

    "income_tax_expense": [
        "IncomeTaxExpenseBenefit"
    ],


    "pretax_income": [
        "IncomeBeforeTaxExpenseBenefit",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxes",
        "PretaxIncome",
        "EarningsBeforeTax",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"
    ]

},

"balance_sheet": {

    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],

    "accounts_receivable": [
        "AccountsReceivableNetCurrent",
        "ReceivablesNetCurrent",
        "AccountsReceivableNet",
        "TradeAccountsReceivableNetCurrent",
        "AccountsNotesAndLoansReceivableNetCurrent"
    ],

    "inventory": [
        "InventoryNet",
        "InventoriesNet",
        "InventoryGross",
    ],

    "total_assets": [
        "Assets",
        "AssetsTotal"
    ],

    "total_liabilities": [
        "Liabilities",
        "LiabilitiesTotal",
        "TotalLiabilities"
    ],

    "shareholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "StockholdersEquityAttributableToParent",
        "StockholdersEquityIncludingPortionAttributableToParent",
        "Equity"
    ],

    "debt": [
        "Debt",
        "DebtAndCapitalLeaseObligations",
        "DebtAndFinanceLeaseObligations",
        "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
        "LongTermDebtAndFinanceLeaseObligationsIncludingCurrentMaturities"
    ],

    "debt_current": [
        "DebtCurrent",
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "LongTermDebtAndCapitalLeaseObligationsCurrent",
        "LongTermDebtCurrent",
        "ShortTermBorrowings",
        "CommercialPaper"
    ],

    "debt_noncurrent": [
        "LongTermDebtAndFinanceLeaseObligations",
        "LongTermDebtAndCapitalLeaseObligations",
        "LongTermDebtNoncurrent",
        "LongTermDebt"
    ],

    "accounts_payable": [
        "AccountsPayable",
        "AccountsPayableCurrent",
        "AccountsPayableTradeCurrent"
    ],

    "accrued_liabilities": [
        "AccruedLiabilities",
        "AccruedLiabilitiesCurrent",
        "OtherAccruedLiabilitiesCurrent"
        "AccruedExpensesAndOtherCurrentLiabilities"
    ],

    "accounts_payable+accrued_liabilities": [
        "AccountsPayableAndAccruedLiabilitiesCurrent",
        "AccountsPayableAndOtherAccruedLiabilitiesCurrent",
    ],

    "deferred_revenue": [
        "ContractWithCustomerLiabilityCurrent",
        "DeferredRevenueCurrent",
        "CustomerAdvancesCurrent"
    ],

    "taxes_payable": [
        "IncomeTaxesPayableCurrent",
        "TaxesPayableCurrent"
    ]
},

"cashflow_statement": {

    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        "CashProvidedByUsedInOperatingActivities"
    ],

    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "CapitalExpenditures",
        "PaymentsForProceedsFromPropertyPlantAndEquipment",
        "PaymentsToAcquirePropertyPlantAndEquipmentAndIntangibleAssets"
    ]

}

}