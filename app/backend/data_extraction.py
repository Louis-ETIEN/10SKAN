import time
from datetime import datetime
import requests
import yfinance as yf
from copy import deepcopy
from schema import SCHEMA, SCHEMA_MM, SCHEMA_MYM
from tag_map import TAG_MAP
import json


HEADERS_SEC = {
    "User-Agent": "Louis Etien louis-etien@hotmail.fr"
}

def get_filing_url(cik):
    submission_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    r = requests.get(submission_url, headers=HEADERS_SEC)
    data = r.json()
    time.sleep(0.1) # SEC has a 10 requests/sec limit

    filings = data["filings"]["recent"]

    forms = filings["form"]
    accessions = filings["accessionNumber"]
    documents = filings["primaryDocument"]

    accession = None
    document = None

    for i, form in enumerate(forms):
        if form == "10-K":
            accession = accessions[i].replace("-", "")
            document = documents[i]
            break

    if not accession:
        return None
    
    cik_no_zero = str(int(cik))

    return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{accession}/{document}"
    
def get_company_facts(cik: str):

    cik = cik.zfill(10)

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

    response = requests.get(url, headers=HEADERS_SEC)

    response.raise_for_status()

    return response.json()

def fiscal_year(end):

    d = datetime.strptime(end, "%Y-%m-%d")

    # January fiscal year endings belong to previous FY
    if d.month <= 2:
        return str(d.year - 1)

    return str(d.year)

def is_full_year(start, end):
    start = datetime.strptime(start, "%Y-%m-%d")
    end = datetime.strptime(end, "%Y-%m-%d")

    days = (end - start).days

    return 350 <= days <= 380

def get_years(facts, n_years=11):

    years = set()

    assets_entries = facts["facts"]["us-gaap"]["Assets"]["units"]["USD"]

    entries = [e for e in assets_entries if e.get("form") == "10-K"]

    for e in entries:
        years.add(fiscal_year(e["end"]))

    years = list(years) 

    years.sort(reverse=True)

    return years[:n_years]

def get_facts(facts, tag, section, year):

    try:

        if tag in (TAG_MAP["income_statement"]["weighted_avg_shares_diluted"]):
            entries = facts["facts"]["us-gaap"][tag]["units"]["shares"]
            for e in entries:
                #if e.get("fp") in ("FY", "Q4") and fiscal_year(e.get("end", "")) == year:
                if e["form"] == "10-K" and "start" in e and "end" in e and \
                is_full_year(e["start"], e["end"]) and fiscal_year(e.get("end", "")) == year:
                    return e.get("val")
                
        if section in ("income_statement", "cashflow_statement"):
            entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
            for e in entries:
                if e["form"] == "10-K" and "start" in e and "end" in e and \
                is_full_year(e["start"], e["end"]) and fiscal_year(e.get("end", "")) == year:
                    return e.get("val")
        else:
            entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]
            for e in entries:
                if e["form"] == "10-K" and fiscal_year(e.get("end", "")) == year:
                    return e.get("val")
        return None

    except KeyError:
        return None
    
def extract_financials(ticker, cik, n_years=11):

    # Fetch the basic numbers from the SEC

    facts = get_company_facts(cik)

    years = get_years(facts, n_years=n_years)

    results = {year: deepcopy(SCHEMA) for year in years}

    results["market_metrics"] = SCHEMA_MM

    results["multi_year_metrics"] = SCHEMA_MYM

    for year in years:
        result = results[year]

        for section in TAG_MAP:

            for metric in TAG_MAP[section]:

                tags = TAG_MAP[section][metric]

                for tag in tags:

                    value = get_facts(facts, tag, section, year)

                    if value is not None:
                        result[section][metric] = value
                        break
        


        # Backup computations if the tags were not all assigned by the company

        if result["cashflow_statement"]["operating_cash_flow"] and \
        result["cashflow_statement"]["capex"]:

            ocf = result["cashflow_statement"]["operating_cash_flow"]
            capex = result["cashflow_statement"]["capex"]

            result["cashflow_statement"]["free_cash_flow"] = ocf - abs(capex)
        
        if not result["income_statement"]["gross_profit"] and result["income_statement"]["revenue"] and result["income_statement"]["cost_of_revenue"]:
            result["income_statement"]["gross_profit"] = result["income_statement"]["revenue"] - result["income_statement"]["cost_of_revenue"]
        
        if not result["balance_sheet"]["shareholders_equity"] and result["balance_sheet"]["total_assets"] and result["balance_sheet"]["total_liabilities"]:
            result["balance_sheet"]["shareholders_equity"] = result["balance_sheet"]["total_assets"] - result["balance_sheet"]["total_liabilities"]

        if not result["balance_sheet"]["total_liabilities"] and result["balance_sheet"]["total_assets"] and result["balance_sheet"]["shareholders_equity"]:
            result["balance_sheet"]["total_liabilities"] = result["balance_sheet"]["total_assets"] - result["balance_sheet"]["shareholders_equity"]

        # Compute derived metrics

        compute_derived_metrics(result)

    # Fetch and compute market metrics from yahoo finance

    compute_market_metrics(ticker, results, revenue=results[years[0]]["income_statement"]["revenue"], fcf=results[years[0]]["cashflow_statement"]["free_cash_flow"])

    # compute multi-year metrics from existing data

    compute_multi_year_metrics(results, years)

    return results

def compute_derived_metrics(result):

    is_ = result["income_statement"]
    bs = result["balance_sheet"]
    cf = result["cashflow_statement"]
    dm = result["derived_metrics"]

    revenue = is_["revenue"]
    gross_profit = is_["gross_profit"]
    operating_income = is_["operating_income"]
    net_income = is_["net_income"]
    weighted_avg_shares_diluted = is_["weighted_avg_shares_diluted"]

    total_assets = bs["total_assets"]
    equity = bs["shareholders_equity"]

    operating_cash_flow = cf["operating_cash_flow"]
    capex = cf["capex"]
    free_cash_flow = cf["free_cash_flow"]


    # Profitability margins

    if revenue and gross_profit:
        dm["gross_margin"] = gross_profit / revenue

    if revenue and operating_income:
        dm["operating_margin"] = operating_income / revenue

    if revenue and net_income:
        dm["net_margin"] = net_income / revenue

    if revenue and free_cash_flow:
        dm["fcf_margin"] = free_cash_flow / revenue

    # per-share

    if net_income and weighted_avg_shares_diluted:
        dm["earnings_per_share"] = net_income / weighted_avg_shares_diluted

    if free_cash_flow and weighted_avg_shares_diluted:
        dm["fcf_per_share"] = free_cash_flow / weighted_avg_shares_diluted

    # Returns

    if net_income and total_assets:
        dm["return_on_assets"] = net_income / total_assets

    if net_income and equity:
        dm["return_on_equity"] = net_income / equity


    # Efficiency

    if revenue and total_assets:
        dm["asset_turnover"] = revenue / total_assets


    # Cash metrics

    if operating_cash_flow and net_income:
        dm["cash_conversion"] = operating_cash_flow / net_income

    if capex and revenue:
        dm["capex_ratio"] = capex / revenue

def compute_market_metrics(ticker, results, revenue, fcf):
    stock = yf.Ticker(ticker)
    info = stock.info

    mm = results["market_metrics"]

    mm["share_price"] = info.get("currentPrice")
    mm["shares_outstanding"] = info.get("sharesOutstanding")
    mm["market_cap"] = info.get("marketCap")
    mm["enterprise_value"] = info.get("enterpriseValue")

    mm["pe_ratio"] = info.get("trailingPE")
    mm["price_to_sales"] = info.get("priceToSalesTrailing12Months")
    mm["price_to_book"] = info.get("priceToBook")

    ev = mm["enterprise_value"]
    market_cap = mm["market_cap"]

    if ev and revenue:
        mm["ev_to_revenue"] = ev / revenue

    if ev and fcf:
        mm["ev_to_fcf"] = ev / fcf

    if market_cap and fcf:
        mm["fcf_yield"] = fcf / market_cap

def compute_cagr(valuet0, valuet1, deltat):
    return ((valuet1 / valuet0) ** (1 / deltat))  - 1

def compute_multi_year_metrics(results, years):

    mym = results["multi_year_metrics"]
    n = len(years)

    def get(path, year):
        """Safely retrieve nested values"""
        try:
            v = results[year]
            for p in path:
                v = v[p]
            return v
        except:
            return None

    def compute_if_valid(metric_key, horizon, start_val, end_val):
        if start_val and end_val and start_val > 0 and end_val > 0:
            mym[metric_key][f"{horizon}y"] = compute_cagr(start_val, end_val, horizon)

    # Revenue CAGR

    if n >= 4:
        start = get(["income_statement", "revenue"], years[3])
        end = get(["income_statement", "revenue"], years[0])
        compute_if_valid("revenue_cagr", 3, start, end)

    if n >= 6:
        start = get(["income_statement", "revenue"], years[5])
        end = get(["income_statement", "revenue"], years[0])
        compute_if_valid("revenue_cagr", 5, start, end)

    if n >= 11:
        start = get(["income_statement", "revenue"], years[10])
        end = get(["income_statement", "revenue"], years[0])
        compute_if_valid("revenue_cagr", 10, start, end)

    # FCF CAGR

    if n >= 4:
        start = get(["cashflow_statement", "free_cash_flow"], years[3])
        end = get(["cashflow_statement", "free_cash_flow"], years[0])
        compute_if_valid("fcf_cagr", 3, start, end)

    if n >= 6:
        start = get(["cashflow_statement", "free_cash_flow"], years[5])
        end = get(["cashflow_statement", "free_cash_flow"], years[0])
        compute_if_valid("fcf_cagr", 5, start, end)

    # Average ROE

    if n >= 5:
        vals = []
        for i in range(5):
            v = get(["derived_metrics", "return_on_equity"], years[i])
            if v:
                vals.append(v)
        if len(vals) == 5:
            mym["avg_roe"]["5y"] = sum(vals) / 5

    if n >= 10:
        vals = []
        for i in range(10):
            v = get(["derived_metrics", "return_on_equity"], years[i])
            if v:
                vals.append(v)
        if len(vals) == 10:
            mym["avg_roe"]["10y"] = sum(vals) / 10

    # Operating Margin Change

    if n >= 4:
        start = get(["derived_metrics", "operating_margin"], years[3])
        end = get(["derived_metrics", "operating_margin"], years[0])
        if start is not None and end is not None:
            mym["operating_margin_change"]["3y"] = end - start

    # Share Count Change: To implement by adding shares outstanding to income statement

    if n >= 4:
        start = get(["market_metrics", "shares_outstanding"], None)
        end = get(["market_metrics", "shares_outstanding"], None)

    if n >= 4:
        start = get(["income_statement", "shares_outstanding"], years[3])
        end = get(["income_statement", "shares_outstanding"], years[0])
        if start and end and start > 0:
            mym["share_count_change"]["3y"] = (end / start) - 1

    if n >= 6:
        start = get(["income_statement", "shares_outstanding"], years[5])
        end = get(["income_statement", "shares_outstanding"], years[0])
        if start and end and start > 0:
            mym["share_count_change"]["5y"] = (end / start) - 1

    # Revenue Volatility (std dev of growth rates)

    if n >= 11:

        growth_rates = []

        for i in range(10):
            r0 = get(["income_statement", "revenue"], years[i])
            r1 = get(["income_statement", "revenue"], years[i + 1])

            if r0 and r1 and r1 > 0:
                growth_rates.append((r0 / r1) - 1)

        if len(growth_rates) == 10:

            mean = sum(growth_rates) / 10
            variance = sum((g - mean) ** 2 for g in growth_rates) / 10
            mym["revenue_volatility"]["10y"] = variance ** 0.5




if __name__ == "__main__":
    #facts = get_company_facts("0000200406") J&J
    # for metric in TAG_MAP["income_statement"]:
    #     print(metric)
    #     for tag in TAG_MAP["income_statement"][metric]:
    #         print(get_facts(facts, tag, "income_statement", "2023"))
    facts= get_company_facts("0001065280")
    for tag in TAG_MAP["income_statement"]["weighted_avg_shares_diluted"]:
        entries = facts["facts"]["us-gaap"][tag]["units"]["shares"]
        print(tag)
        for e in entries:
            if "start" in e and "end" in e and is_full_year(e["start"], e["end"]):
                print(json.dumps(e, indent=4))
    
    #print(get_years(facts, 11))
    #print(json.dumps(get_years(facts, 10), indent=4))
    #print(json.dumps(extract_financials("JNJ", "0000200406", 11), indent=4)) # JNJ test
    #print(json.dumps(extract_financials("AAPL", "0000320193", 11), indent=4)) # Apple test
