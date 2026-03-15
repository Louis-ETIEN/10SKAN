import time
import requests
import yfinance as yf
from copy import deepcopy
from schema import SCHEMA
from tag_map import TAG_MAP


HEADERS_SEC = {
    "User-Agent": "Louis Etien louis-etien@hotmail.fr"
}

def get_filing_url(cik):
    submission_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    r = requests.get(submission_url, headers=HEADERS_SEC)
    data = r.json()
    time.sleep(0.2) # SEC has a 10 requests/sec limit

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

def get_latest_fact(facts, tag):

    try:

        entries = facts["facts"]["us-gaap"][tag]["units"]["USD"]

        annual_entries = [
            e for e in entries
            if e.get("fp") == "FY"
        ]

        if not annual_entries:
            return None

        latest = sorted(
            annual_entries,
            key=lambda x: x["end"]
        )[-1]

        return latest["val"]

    except KeyError:

        return None
    
def extract_financials(ticker, cik):

    # Fetch the basic numbers from the SEC

    facts = get_company_facts(cik)

    result = deepcopy(SCHEMA)

    for section in TAG_MAP:

        for metric in TAG_MAP[section]:

            tags = TAG_MAP[section][metric]

            for tag in tags:

                value = get_latest_fact(facts, tag)

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

    # Compute derived metrics

    compute_derived_metrics(result)

    # Fetch and compute market metrics from yahoo finance

    compute_market_metrics(ticker, result)

    return result

def compute_derived_metrics(result):

    is_ = result["income_statement"]
    bs = result["balance_sheet"]
    cf = result["cashflow_statement"]
    dm = result["derived_metrics"]

    revenue = is_["revenue"]
    gross_profit = is_["gross_profit"]
    operating_income = is_["operating_income"]
    net_income = is_["net_income"]

    total_assets = bs["total_assets"]
    equity = bs["shareholders_equity"]

    operating_cash_flow = cf["operating_cash_flow"]
    capex = cf["capex"]


    # Profitability margins

    if revenue and gross_profit:
        dm["gross_margin"] = gross_profit / revenue

    if revenue and operating_income:
        dm["operating_margin"] = operating_income / revenue

    if revenue and net_income:
        dm["net_margin"] = net_income / revenue


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

def compute_market_metrics(ticker, result):
    stock = yf.Ticker(ticker)
    info = stock.info

    mm = result["market_metrics"]

    mm["share_price"] = info.get("currentPrice")
    mm["shares_outstanding"] = info.get("sharesOutstanding")
    mm["market_cap"] = info.get("marketCap")
    mm["enterprise_value"] = info.get("enterpriseValue")

    mm["pe_ratio"] = info.get("trailingPE")
    mm["price_to_sales"] = info.get("priceToSalesTrailing12Months")
    mm["price_to_book"] = info.get("priceToBook")

    revenue = result["income_statement"]["revenue"]
    fcf = result["cashflow_statement"]["free_cash_flow"]

    ev = mm["enterprise_value"]
    market_cap = mm["market_cap"]

    if ev and revenue:
        mm["ev_to_revenue"] = ev / revenue

    if ev and fcf:
        mm["ev_to_fcf"] = ev / fcf

    if market_cap and fcf:
        mm["fcf_yield"] = fcf / market_cap


if __name__ == "__main__":
    print(extract_financials("0000320193")) 